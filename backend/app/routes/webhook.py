import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from app.models.events import PolymorphicPayload, Incident, IncidentMatch, SeverityLevel, IncidentStatus
from app.database import db_manager
from app.services.embedding import embedding_service
from app.services.vector_search import vector_search_service
from app.services.websocket_manager import ws_manager

logger = logging.getLogger("netpulse.webhook")
router = APIRouter(prefix="/webhook", tags=["Webhook Ingestion"])

@router.post("/ingest")
async def ingest_webhook_payload(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Polymorphic Webhook Ingestion endpoint.
    Accepts arbitrary nested JSON payloads from CI/CD, Docker, K8s, CloudWatch, or custom services.
    Routes telemetry metrics to `raw_events` and errors/crashes to `incidents`.
    """
    try:
        raw_json: Dict[str, Any] = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {str(e)}")

    db = db_manager.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database connection not ready")

    # 1. Normalize core fields while preserving raw payload
    service_name = raw_json.get("service_name") or raw_json.get("service") or raw_json.get("app") or "unknown-service"
    environment = raw_json.get("environment") or raw_json.get("env") or "production"
    level = (raw_json.get("level") or raw_json.get("severity") or "ERROR").upper()
    error_message = raw_json.get("error_message") or raw_json.get("message") or raw_json.get("error") or ""
    stack_trace = raw_json.get("stack_trace") or raw_json.get("trace") or raw_json.get("exception") or ""
    
    # Normalize timestamp
    raw_ts = raw_json.get("timestamp") or raw_json.get("time") or raw_json.get("created_at")
    timestamp = datetime.utcnow()
    if raw_ts:
        try:
            if isinstance(raw_ts, str):
                timestamp = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
        except Exception:
            timestamp = datetime.utcnow()

    # 2. Check if this is a high-frequency telemetry / heartbeat metric event
    metrics = raw_json.get("metrics")
    if metrics and isinstance(metrics, dict) and not error_message and level not in ["ERROR", "CRITICAL", "FATAL"]:
        metric_docs = []
        for metric_name, val in metrics.items():
            try:
                numeric_val = float(val)
                metric_docs.append({
                    "service_name": service_name,
                    "timestamp": timestamp,
                    "metric_type": metric_name,
                    "value": numeric_val,
                    "metadata": {"source": raw_json.get("source", "telemetry")}
                })
            except (ValueError, TypeError):
                continue
        if metric_docs:
            await db["raw_events"].insert_many(metric_docs)
            return {"status": "ingested", "type": "telemetry", "count": len(metric_docs)}

    # Also record any metrics accompanying an incident
    if metrics and isinstance(metrics, dict):
        metric_docs = []
        for metric_name, val in metrics.items():
            try:
                metric_docs.append({
                    "service_name": service_name,
                    "timestamp": timestamp,
                    "metric_type": metric_name,
                    "value": float(val),
                    "metadata": {"source": raw_json.get("source", "crash-telemetry")}
                })
            except (ValueError, TypeError):
                continue
        if metric_docs:
            background_tasks.add_task(db["raw_events"].insert_many, metric_docs)

    # 3. Process as Incident
    if not error_message and stack_trace:
        error_message = stack_trace.strip().split("\n")[-1]
    elif not error_message:
        error_message = f"Critical incident detected in {service_name}"

    clean_trace = embedding_service.normalize_text(error_message, stack_trace)
    
    # Generate 768-dim vector embedding
    embedding = await embedding_service.get_embedding(f"{error_message}\n{clean_trace}")
    
    # Query Vector Search for Top 3 similar historical incidents
    similar_incidents = await vector_search_service.find_similar_incidents(
        query_vector=embedding,
        top_k=3
    )

    # Find matched runbook
    matched_runbook_id = None
    if similar_incidents and similar_incidents[0].get("runbook_id"):
        matched_runbook_id = similar_incidents[0]["runbook_id"]
    else:
        # Match by error signature keyword or service
        rb = await db["runbooks"].find_one({
            "$or": [
                {"service_name": service_name},
                {"category": {"$regex": service_name, "$options": "i"}}
            ]
        })
        if rb:
            matched_runbook_id = rb.get("runbook_id")

    # Fetch matched runbook document if present
    matched_runbook_doc = None
    if matched_runbook_id:
        matched_runbook_doc = await db["runbooks"].find_one({"runbook_id": matched_runbook_id}, {"_id": 0})

    # AI Root-Cause Synthesis
    top_match = similar_incidents[0] if similar_incidents else None
    root_cause = await embedding_service.synthesize_root_cause(
        incident_data={"service_name": service_name, "error_message": error_message, "normalized_stack_trace": clean_trace},
        matched_incident=top_match,
        runbook=matched_runbook_doc
    )

    # Calculate blast radius
    severity = SeverityLevel.P1 if level in ["CRITICAL", "FATAL"] else (
        SeverityLevel.P2 if level == "ERROR" else SeverityLevel.P3
    )

    incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    title = f"{service_name}: {error_message[:60]}"
    
    # Git metadata
    git_meta = raw_json.get("git_metadata") or raw_json.get("git") or {}

    incident_doc = {
        "incident_id": incident_id,
        "title": title,
        "service_name": service_name,
        "environment": environment,
        "severity": severity.value,
        "status": IncidentStatus.ACTIVE.value,
        "error_message": error_message,
        "normalized_stack_trace": clean_trace,
        "raw_stack_trace": stack_trace,
        "source": raw_json.get("source", "webhook"),
        "git_metadata": git_meta,
        "embedding": embedding,
        "suggested_runbook_id": matched_runbook_id,
        "top_matches": similar_incidents,
        "root_cause_summary": root_cause,
        "raw_payload": raw_json,
        "created_at": timestamp,
        "updated_at": timestamp
    }

    await db["incidents"].insert_one(incident_doc)

    # Broadcast over WebSocket to all live command center clients
    safe_broadcast_doc = {k: v for k, v in incident_doc.items() if k not in ["_id", "embedding"]}
    safe_broadcast_doc["created_at"] = timestamp.isoformat()
    safe_broadcast_doc["updated_at"] = timestamp.isoformat()
    
    await ws_manager.broadcast("new_incident", safe_broadcast_doc)

    return {
        "status": "ingested",
        "type": "incident",
        "incident_id": incident_id,
        "service_name": service_name,
        "deduplication_match": {
            "has_match": len(similar_incidents) > 0,
            "top_match_id": top_match["incident_id"] if top_match else None,
            "similarity_score": top_match["similarity_score"] if top_match else 0.0,
            "similarity_percentage": f"{int((top_match['similarity_score'] if top_match else 0) * 100)}%"
        },
        "suggested_runbook_id": matched_runbook_id,
        "root_cause_preview": root_cause[:120] + "..." if len(root_cause) > 120 else root_cause,
        "triage_url": f"/api/incidents/{incident_id}/triage"
    }
