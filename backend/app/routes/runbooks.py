import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.database import db_manager
from app.services.remediation import remediation_service

logger = logging.getLogger("netpulse.runbooks")
router = APIRouter(prefix="/runbooks", tags=["Runbooks & Self-Healing"])

class ExecuteRunbookRequest(BaseModel):
    incident_id: str

@router.get("")
async def list_runbooks(
    service_name: Optional[str] = None,
    category: Optional[str] = None
):
    """Retrieves all verified runbooks."""
    db = db_manager.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not ready")

    query = {}
    if service_name:
        query["service_name"] = service_name
    if category:
        query["category"] = category

    cursor = db["runbooks"].find(query, {"_id": 0})
    runbooks = await cursor.to_list(length=100)
    return runbooks

@router.get("/{runbook_id}")
async def get_runbook(runbook_id: str):
    """Retrieves a specific runbook by ID."""
    db = db_manager.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not ready")

    rb = await db["runbooks"].find_one({"runbook_id": runbook_id}, {"_id": 0})
    if not rb:
        raise HTTPException(status_code=404, detail=f"Runbook {runbook_id} not found")
    return rb

@router.post("/{runbook_id}/execute")
async def execute_runbook_action(
    runbook_id: str,
    payload: ExecuteRunbookRequest,
    background_tasks: BackgroundTasks
):
    """
    Executes or simulates automated self-healing remediation.
    Streams execution steps to WebSocket and transitions incident to RESOLVED.
    """
    db = db_manager.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not ready")

    incident = await db["incidents"].find_one({"incident_id": payload.incident_id})
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {payload.incident_id} not found")

    # Execute remediation
    result = await remediation_service.execute_runbook(runbook_id, payload.incident_id)
    return result
