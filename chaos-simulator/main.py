import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from scenarios import CHAOS_SCENARIOS
from simulator import trigger_chaos_outage, send_telemetry_heartbeat

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [ChaosService]: %(message)s")
logger = logging.getLogger("ChaosService")

app = FastAPI(title="NetPulse Chaos Simulator Service", version="1.0.0")

def get_backend_url() -> str:
    # Injected via Vercel service binding env "BACKEND_URL"
    return os.getenv("BACKEND_URL", "http://backend:8000").rstrip("/")

class TriggerRequest(BaseModel):
    scenario: str = "db_pool_exhaustion"

@app.get("/")
def root():
    return {
        "service": "chaos-simulator",
        "status": "online",
        "backend_binding_configured": bool(os.getenv("BACKEND_URL")),
        "backend_url": get_backend_url()
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "backend_target": get_backend_url()
    }

@app.get("/scenarios")
def list_scenarios():
    return [
        {"id": k, "service": v["service_name"], "level": v["level"], "error": v["error_message"]}
        for k, v in CHAOS_SCENARIOS.items()
    ]

@app.post("/trigger")
def trigger_scenario(payload: TriggerRequest):
    if payload.scenario not in CHAOS_SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario '{payload.scenario}'. Available: {list(CHAOS_SCENARIOS.keys())}"
        )
    backend_url = get_backend_url()
    client = httpx.Client(base_url=backend_url)
    try:
        trigger_chaos_outage(client, payload.scenario)
        return {
            "status": "success",
            "scenario": payload.scenario,
            "backend_url": backend_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger outage on backend: {str(e)}")
