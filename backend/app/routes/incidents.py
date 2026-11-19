import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from app.database import db_manager
from app.services.aggregation import aggregation_service
from app.services.vector_search import vector_search_service

logger = logging.getLogger("netpulse.incidents")
router = APIRouter(prefix="/incidents", tags=["Incidents"])

@router.get("")
async def list_incidents(
    status: Optional[str] = Query(None, description="ACTIVE, TRIAGED, REMEDIATING, RESOLVED"),
    severity: Optional[str] = Query(None, description="P1-Critical, P2-High, P3-Medium"),
    service_name: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """Lists incidents with optional filtering by status, severity, or service."""
    db = db_manager.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not ready")

    query = {}
    if status:
        query["status"] = status
    if severity:
        query["severity"] = severity
    if service_name:
        query["service_name"] = service_name

    cursor = db["incidents"].find(
        query,
        {"_id": 0, "embedding": 0}
    ).sort("created_at", -1).skip(skip).limit(limit)

    incidents = await cursor.to_list(length=limit)
    total_count = await db["incidents"].count_documents(query)

    return {
        "total": total_count,
        "count": len(incidents),
        "incidents": incidents
    }

@router.get("/{incident_id}")
async def get_incident(incident_id: str):
    """Retrieves a single incident by ID."""
    db = db_manager.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not ready")

    doc = await db["incidents"].find_one({"incident_id": incident_id}, {"_id": 0, "embedding": 0})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    return doc

@router.get("/{incident_id}/triage")
async def get_incident_triage(incident_id: str):
    """
    Detailed Causal Timeline & Blast Radius Triage endpoint.
    Uses MongoDB Aggregation Pipeline ($match, $bucket/$group, $lookup, $sort) to reconstruct
    pre-crash metric spike timeline, upstream/downstream blast radius, and top similar past outages.
    """
    db = db_manager.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not ready")

    # 1. Fetch incident with runbook lookup
    incident_data = await aggregation_service.get_incident_triage_data(incident_id)
    if not incident_data:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    service_name = incident_data.get("service_name", "unknown")
    crash_time = incident_data.get("created_at", datetime.utcnow())
    embedding = incident_data.get("embedding", [])
    
    # 2. Reconstruct Pre-Crash Metric Spike Timeline (15 min window)
    timeline = await aggregation_service.get_pre_crash_timeline(
        service_name=service_name,
        crash_timestamp=crash_time,
        window_minutes=15
    )

    # 3. Find Top 3 Similar Past Outages (excluding current incident)
    similar_incidents = []
    if embedding:
        similar_incidents = await vector_search_service.find_similar_incidents(
            query_vector=embedding,
            top_k=3,
            exclude_incident_id=incident_id
        )

    # 4. Service Dependency & Blast Radius Topology
    topology = await aggregation_service.get_service_topology(active_service=service_name)

    # Matched runbook details
    matched_rb = incident_data.get("matched_runbook")
    
    # Clean embedding from incident response
    incident_data.pop("embedding", None)

    return {
        "incident": incident_data,
        "similar_past_outages": similar_incidents,
        "matched_runbook": matched_rb,
        "causal_timeline": [p.model_dump() for p in timeline],
        "affected_topology": topology,
        "ai_root_cause_analysis": incident_data.get("root_cause_summary") or "Automated root-cause analysis completed.",
        "suggested_action": f"Apply Runbook '{matched_rb.get('title')}'" if matched_rb else "Investigate upstream dependencies."
    }
