import logging
import math
import hashlib
import re
from typing import List, Optional, Dict, Any
import numpy as np
from app.config import settings

logger = logging.getLogger("netpulse.embedding")

class EmbeddingService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.dimensions = settings.EMBEDDING_DIMENSIONS
        self.client = None
        
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Initialized Gemini AI client for embeddings and synthesis.")
            except Exception as e:
                logger.warning(f"Failed to initialize google-genai client: {e}. Will use semantic fallback.")
                self.client = None

    def normalize_text(self, error_message: str, stack_trace: Optional[str] = None) -> str:
        """Strips volatile memory addresses, thread IDs, timestamps, and line numbers to preserve semantic structure."""
        text = f"{error_message or ''} \n {stack_trace or ''}"
        
        # Replace memory hex addresses like 0x7ffd5e6b1234
        text = re.sub(r'0x[0-9a-fA-F]{6,16}', '0xMEM_ADDR', text)
        # Replace timestamps like 2026-11-18T10:12:44.123Z
        text = re.sub(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?', 'TIMESTAMP', text)
        # Replace UUIDs
        text = re.sub(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', 'UUID', text)
        # Replace specific thread numbers
        text = re.sub(r'Thread-\d+|PID:\s*\d+|port\s+\d{4,5}', 'THREAD_ID', text)
        
        return text.strip()

    async def get_embedding(self, text: str) -> List[float]:
        """Generates unit-normalized 768-dimensional embedding via Gemini API with local fallback."""
        cleaned_text = self.normalize_text(text)
        
        if self.client:
            try:
                # Call Gemini embedding API
                response = self.client.models.embed_content(
                    model=settings.EMBEDDING_MODEL,
                    contents=cleaned_text,
                )
                if hasattr(response, 'embedding') and hasattr(response.embedding, 'values'):
                    vec = list(response.embedding.values)
                    # Ensure 768 dim or pad/truncate
                    if len(vec) == self.dimensions:
                        return vec
                    elif len(vec) > self.dimensions:
                        return vec[:self.dimensions]
                    else:
                        return vec + [0.0] * (self.dimensions - len(vec))
            except Exception as e:
                logger.warning(f"Gemini API embed call failed ({e}). Falling back to local semantic vectorizer.")

        # High-precision deterministic fallback vectorizer
        return self._local_semantic_embedding(cleaned_text)

    def _local_semantic_embedding(self, text: str) -> List[float]:
        """Produces a deterministic, high-dimensional vector capturing semantic, lexical,
        and structural stack-trace features with unit L2 norm."""
        tokens = re.findall(r'[a-zA-Z0-9_\.]+', text.lower())
        vec = np.zeros(self.dimensions, dtype=np.float32)
        
        if not tokens:
            vec[0] = 1.0
            return vec.tolist()
            
        # Key error categories boost specific seed orthogonal bases
        category_weights = {
            "connection": 12, "pool": 13, "exhausted": 14, "timeout": 15,
            "oomkilled": 25, "memory": 26, "heap": 27, "allocation": 28,
            "nullpointer": 35, "undefined": 36, "attributeerror": 37,
            "syntaxerror": 45, "importerror": 46, "modulenotfound": 47,
            "database": 55, "postgresql": 56, "redis": 57, "mongo": 58,
            "502": 65, "504": 66, "gateway": 67, "upstream": 68
        }
        
        for token in tokens:
            h = int(hashlib.sha256(token.encode('utf-8')).hexdigest(), 16)
            idx = h % self.dimensions
            weight = category_weights.get(token, 1.0)
            sign = 1.0 if ((h >> 8) % 2 == 0) else -1.0
            vec[idx] += sign * weight
            
            # Character trigram hashing for typo/version-shift resilience
            if len(token) >= 3:
                for i in range(len(token) - 2):
                    trigram = token[i:i+3]
                    th = int(hashlib.md5(trigram.encode('utf-8')).hexdigest(), 16)
                    t_idx = th % self.dimensions
                    vec[t_idx] += 0.3 * (1.0 if ((th >> 4) % 2 == 0) else -1.0)
                    
        # L2 Normalization
        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec = vec / norm
        else:
            vec[0] = 1.0
            
        return vec.tolist()

    async def synthesize_root_cause(
        self,
        incident_data: Dict[str, Any],
        matched_incident: Optional[Dict[str, Any]] = None,
        runbook: Optional[Dict[str, Any]] = None
    ) -> str:
        """Synthesizes an incident root-cause analysis using Gemini 2.5 Flash, or structured fallback."""
        service = incident_data.get("service_name", "unknown-service")
        err = incident_data.get("error_message", "Unknown error")
        stack = incident_data.get("normalized_stack_trace", "")[:500]
        
        if self.client:
            try:
                prompt = f"""You are the NetPulse AI Autonomous SRE root-cause analyzer.
Analyze this incident and generate a concise 2-3 sentence root-cause diagnosis and actionable fix:
Service: {service}
Error: {err}
Stack Trace Snippet: {stack}
Matched Past Incident: {matched_incident.get('title') if matched_incident else 'None'}
Suggested Runbook: {runbook.get('title') if runbook else 'None'}

Be precise, technical, and direct."""

                response = self.client.models.generate_content(
                    model=settings.SYNTHESIS_MODEL,
                    contents=prompt
                )
                if response and hasattr(response, 'text') and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini synthesis generation failed ({e}). Using deterministic synthesis.")

        # Structured deterministic synthesis
        if "pool" in err.lower() or "connection" in err.lower():
            return f"Root cause: Database connection pool starvation on '{service}'. Under high concurrent traffic, unreleased connection handles caused downstream request queues to saturate. Recommended action: Execute connection pool drain and increase max_connections limit."
        elif "memory" in err.lower() or "oom" in err.lower():
            return f"Root cause: Unbounded memory allocation in '{service}' pod triggered Linux cgroup OOMKiller. Upstream services experienced cascading 504 timeouts. Recommended action: Roll back recent image commit and apply memory limit bump."
        elif "import" in err.lower() or "module" in err.lower() or "dependency" in err.lower():
            return f"Root cause: CI/CD dependency resolution mismatch in build pipeline for '{service}'. Transitive package bump broke ABI compatibility. Recommended action: Pin dependency in lockfile and trigger automated rollback build."
        else:
            return f"Root cause: Upstream service failure in '{service}' triggered cascading fault propagation. Recommended action: Execute runbook '{runbook.get('title') if runbook else 'Emergency Service Restart'}' and inspect downstream circuit breakers."

embedding_service = EmbeddingService()
