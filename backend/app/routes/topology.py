import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.services.aggregation import aggregation_service

logger = logging.getLogger("netpulse.topology")
router = APIRouter(prefix="/services", tags=["Service Topology"])

@router.get("/topology")
async def get_services_topology(
    active_service: Optional[str] = Query(None, description="Optional active crashing service to highlight blast radius")
):
    """Returns microservice topology graph with live health status, failure blast radius, and edge latencies."""
    return await aggregation_service.get_service_topology(active_service=active_service)
