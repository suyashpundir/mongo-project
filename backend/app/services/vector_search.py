import logging
from typing import List, Dict, Any, Optional
import numpy as np
from app.database import db_manager
from app.config import settings

logger = logging.getLogger("netpulse.vector_search")

class VectorSearchService:
    async def find_similar_incidents(
        self,
        query_vector: List[float],
        top_k: int = 3,
        exclude_incident_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Finds top similar past incidents using MongoDB Atlas $vectorSearch with fallback to local cosine similarity."""
        db = db_manager.db
        if db is None:
            return []

        # 1. Try MongoDB Atlas $vectorSearch if available
        if db_manager.is_atlas_vector_search_ready:
            try:
                pipeline = [
                    {
                        "$vectorSearch": {
                            "index": "vector_index",
                            "path": "embedding",
                            "queryVector": query_vector,
                            "numCandidates": 50,
                            "limit": top_k + (1 if exclude_incident_id else 0)
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "incident_id": 1,
                            "title": 1,
                            "service_name": 1,
                            "severity": 1,
                            "status": 1,
                            "error_message": 1,
                            "created_at": 1,
                            "runbook_id": "$suggested_runbook_id",
                            "similarity_score": {"$meta": "vectorSearchScore"}
                        }
                    }
                ]
                
                cursor = db["incidents"].aggregate(pipeline)
                results = await cursor.to_list(length=top_k + 2)
                
                filtered = [
                    r for r in results 
                    if not exclude_incident_id or r.get("incident_id") != exclude_incident_id
                ][:top_k]
                
                if filtered:
                    return filtered
            except Exception as e:
                logger.warning(f"Atlas Vector Search aggregate failed ({e}). Falling back to in-memory cosine search.")

        # 2. Local In-Memory Cosine Similarity Fallback
        return await self._local_cosine_similarity_search(query_vector, top_k, exclude_incident_id)

    async def _local_cosine_similarity_search(
        self,
        query_vector: List[float],
        top_k: int = 3,
        exclude_incident_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        db = db_manager.db
        if db is None:
            return []

        cursor = db["incidents"].find(
            {"embedding": {"$exists": True, "$ne": []}},
            {
                "_id": 0,
                "incident_id": 1,
                "title": 1,
                "service_name": 1,
                "severity": 1,
                "status": 1,
                "error_message": 1,
                "created_at": 1,
                "suggested_runbook_id": 1,
                "embedding": 1
            }
        ).sort("created_at", -1).limit(100)
        
        candidates = await cursor.to_list(length=100)
        if not candidates:
            return []
            
        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 1e-6:
            q_vec = q_vec / q_norm
        else:
            return []

        scored = []
        for doc in candidates:
            inc_id = doc.get("incident_id")
            if exclude_incident_id and inc_id == exclude_incident_id:
                continue
                
            emb = doc.get("embedding")
            if not emb or len(emb) != len(query_vector):
                continue
                
            c_vec = np.array(emb, dtype=np.float32)
            c_norm = np.linalg.norm(c_vec)
            if c_norm > 1e-6:
                c_vec = c_vec / c_norm
                
            # Cosine similarity
            similarity = float(np.dot(q_vec, c_vec))
            # Rescale / clip to [0.0, 1.0]
            similarity_clamped = max(0.0, min(1.0, (similarity + 1.0) / 2.0 if similarity < 0 else similarity))
            
            scored.append({
                "incident_id": inc_id,
                "title": doc.get("title", f"Incident {inc_id}"),
                "service_name": doc.get("service_name", "unknown"),
                "severity": doc.get("severity", "P2-High"),
                "status": doc.get("status", "RESOLVED"),
                "error_message": doc.get("error_message", ""),
                "created_at": doc.get("created_at"),
                "runbook_id": doc.get("suggested_runbook_id"),
                "similarity_score": round(similarity_clamped, 4)
            })

        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored[:top_k]

vector_search_service = VectorSearchService()
