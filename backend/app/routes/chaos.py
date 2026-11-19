import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.database import db_manager
from app.services.websocket_manager import ws_manager
from app.services.embedding import embedding_service
from app.services.vector_search import vector_search_service

logger = logging.getLogger("netpulse.chaos")
router = APIRouter(prefix="/chaos", tags=["Chaos Simulator"])

CHAOS_SCENARIOS = {
    "db_pool_exhaustion": {
        "id": "db_pool_exhaustion",
        "title": "DB Connection Pool Exhaustion -> Auth Service Timeout -> Checkout 502",
        "service_name": "checkout-api",
        "environment": "production",
        "level": "CRITICAL",
        "error_message": "PostgreSQL connection pool exhausted: timeout waiting for connection (max_connections=100 exceeded by pool 'auth-checkout')",
        "stack_trace": """Traceback (most recent call last):
  File "/app/services/checkout.py", line 184, in create_order
    user = await auth_client.verify_token(token)
  File "/app/clients/auth.py", line 62, in verify_token
    session = await db.fetch_row("SELECT * FROM sessions WHERE token = $1", token)
  File "/usr/local/lib/python3.11/site-packages/asyncpg/pool.py", line 402, in acquire
    raise exceptions.TooManyConnectionsError('PostgreSQL connection pool exhausted: timeout waiting for connection')
asyncpg.exceptions.TooManyConnectionsError: PostgreSQL connection pool exhausted: timeout waiting for connection (max_connections=100 exceeded by pool 'auth-checkout')""",
        "git_metadata": {
            "commit_hash": "a4f89d2",
            "branch": "main",
            "author": "devops-engineer@company.com",
            "commit_message": "feat(checkout): parallelize inventory and auth checks without connection pooling limit",
            "diff_summary": "+++ b/services/checkout.py\n@@ -180,3 +180,6 @@\n+ tasks = [auth_client.verify_token(token), inventory.reserve(items)]\n+ await asyncio.gather(*tasks)"
        },
        "metrics_ramp": [
            {"cpu": 35.0, "mem": 480.0, "lat": 45.0, "err": 0.0, "active_conn": 45},
            {"cpu": 52.0, "mem": 520.0, "lat": 180.0, "err": 1.2, "active_conn": 90},
            {"cpu": 78.0, "mem": 650.0, "lat": 850.0, "err": 8.5, "active_conn": 100},
            {"cpu": 96.5, "mem": 820.0, "lat": 3200.0, "err": 44.0, "active_conn": 100}
        ]
    },
    "bad_ci_dependency": {
        "id": "bad_ci_dependency",
        "title": "Bad CI Dependency Bump Breaking Build (Docker / GitHub Actions)",
        "service_name": "ci-cd-builder",
        "environment": "production",
        "level": "FATAL",
        "error_message": "CI Build Failure: ModuleNotFoundError: No module named 'cryptography.hazmat.bindings._rust' during Docker container compilation",
        "stack_trace": """Step 8/14 : RUN pip install -r requirements.txt
Collecting cryptography>=42.0.0 (from -r requirements.txt (line 14))
  Downloading cryptography-42.0.5.tar.gz (10.8 MB)
  Installing build dependencies ... done
  Getting requirements to build wheel ... error
  error: subprocess-exited-with-error
  running bdist_wheel
  running build
  running build_py
  running build_ext
  fatal error: Rust compiler 'cargo' not found in alpine-slim container
  ModuleNotFoundError: No module named 'cryptography.hazmat.bindings._rust'
The command '/bin/sh -c pip install -r requirements.txt' returned a non-zero code: 1
GitHub Actions Job 'build-and-deploy' terminated with exit code 1""",
        "git_metadata": {
            "commit_hash": "c71e04b",
            "branch": "main",
            "author": "dependabot[bot]",
            "commit_message": "build(deps): bump cryptography from 41.0.7 to 42.0.5 in backend",
            "diff_summary": "+++ b/backend/requirements.txt\n@@ -14,1 +14,1 @@\n-cryptography==41.0.7\n+cryptography>=42.0.0"
        },
        "metrics_ramp": [
            {"cpu": 20.0, "mem": 300.0, "lat": 15.0, "err": 0.0, "active_conn": 10},
            {"cpu": 65.0, "mem": 450.0, "lat": 40.0, "err": 5.0, "active_conn": 15},
            {"cpu": 98.0, "mem": 890.0, "lat": 120.0, "err": 100.0, "active_conn": 2}
        ]
    },
    "memory_leak_oom": {
        "id": "memory_leak_oom",
        "title": "Memory Leak / K8s OOMKilled -> Payment Gateway Cascading Retry Storm",
        "service_name": "payment-gateway",
        "environment": "production",
        "level": "CRITICAL",
        "error_message": "Kubernetes Pod OOMKilled: container 'payment-worker' exceeded memory limit (2048Mi) and was terminated with exit code 137",
        "stack_trace": """Kubelet log: 2026-11-18T10:15:22.412Z node-worker-pool-3 kernel: [ 4812.912] Memory cgroup out of memory: Killed process 38192 (python) total-vm:2841024kB, anon-rss:2088960kB
container payment-worker in pod payment-gateway-7b9c6f849d-v9x2l OOMKilled
upstream-caller: checkout-api received HTTP 504 Gateway Timeout
payment-gateway circuit breaker: OPEN due to consecutive pod termination events""",
        "git_metadata": {
            "commit_hash": "e12f980",
            "branch": "main",
            "author": "payment-team@company.com",
            "commit_message": "fix(cache): cache idempotency tokens in memory without LRU eviction TTL",
            "diff_summary": "+++ b/services/payment/idempotency.py\n@@ -42,3 +42,3 @@\n- cache = ExpiringLRUDict(ttl_seconds=3600)\n+ cache = {}\n+ cache[token] = payload"
        },
        "metrics_ramp": [
            {"cpu": 40.0, "mem": 600.0, "lat": 65.0, "err": 0.1, "active_conn": 80},
            {"cpu": 62.0, "mem": 1200.0, "lat": 140.0, "err": 1.5, "active_conn": 150},
            {"cpu": 88.0, "mem": 1850.0, "lat": 620.0, "err": 12.0, "active_conn": 320},
            {"cpu": 99.0, "mem": 2048.0, "lat": 4800.0, "err": 52.0, "active_conn": 540}
        ]
    },
    "cache_partition": {
        "id": "cache_partition",
        "title": "Redis Cache Eviction Storm -> Database Connection Flooding",
        "service_name": "auth-service",
        "environment": "production",
        "level": "CRITICAL",
        "error_message": "RedisConnectionError: OOM command not allowed when used memory > 'maxmemory' (maxmemory_policy=noeviction) causing cascading auth cache miss storms",
        "stack_trace": """redis.exceptions.ResponseError: OOM command not allowed when used memory > 'maxmemory'.
  File "/app/services/session.py", line 89, in store_jwt_session
    await redis.set(f"session:{user_id}", data)
redis.exceptions.ConnectionError: Redis node at redis-cluster-master:6379 rejecting writes.
Cascading failure: auth-service fell back to querying postgres-auth for every single request (5,000 req/s), saturating DB CPU to 100%.""",
        "git_metadata": {
            "commit_hash": "771ca81",
            "branch": "main",
            "author": "infra-team@company.com",
            "commit_message": "chore(redis): set maxmemory policy to noeviction for session integrity",
            "diff_summary": "+++ b/k8s/redis-configmap.yaml\n@@ -12,1 +12,1 @@\n-maxmemory-policy allkeys-lru\n+maxmemory-policy noeviction"
        },
        "metrics_ramp": [
            {"cpu": 30.0, "mem": 512.0, "lat": 25.0, "err": 0.0, "active_conn": 40},
            {"cpu": 70.0, "mem": 850.0, "lat": 320.0, "err": 4.5, "active_conn": 210},
            {"cpu": 98.0, "mem": 1024.0, "lat": 2800.0, "err": 39.0, "active_conn": 480}
        ]
    }
}

class ChaosRequest(BaseModel):
    scenario: str = "db_pool_exhaustion"
    custom_target_service: Optional[str] = None

@router.get("/scenarios")
async def list_chaos_scenarios():
    """Lists available chaos simulation scenarios."""
    return [
        {
            "id": k,
            "title": v["title"],
            "service_name": v["service_name"],
            "level": v["level"],
            "error_message": v["error_message"]
        }
        for k, v in CHAOS_SCENARIOS.items()
    ]

@router.post("/trigger")
async def trigger_chaos_scenario(
    payload: ChaosRequest,
    background_tasks: BackgroundTasks
):
    """
    Triggers a cascading failure simulation.
    Ingests pre-crash metric ramps into `raw_events`, triggers the crash incident,
    performs vector search deduplication, and broadcasts over WebSocket in real time.
    """
    scenario = CHAOS_SCENARIOS.get(payload.scenario)
    if not scenario:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario '{payload.scenario}'. Available: {list(CHAOS_SCENARIOS.keys())}"
        )

    db = db_manager.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not ready")

    service_name = payload.custom_target_service or scenario["service_name"]
    now = datetime.utcnow()

    # 1. Ingest realistic pre-crash metric ramp into raw_events
    metric_docs = []
    ramp = scenario.get("metrics_ramp", [])
    step_count = len(ramp)
    for idx, m in enumerate(ramp):
        ts = now - timedelta(minutes=(step_count - idx) * 3)
        for metric_type, val in [
            ("cpu_percent", m["cpu"]),
            ("memory_mb", m["mem"]),
            ("latency_ms", m["lat"]),
            ("error_rate", m["err"]),
            ("active_connections", m["active_conn"]),
        ]:
            metric_docs.append({
                "service_name": service_name,
                "timestamp": ts,
                "metric_type": metric_type,
                "value": float(val),
                "metadata": {"source": "chaos-simulator", "scenario": scenario["id"]}
            })

    if metric_docs:
        await db["raw_events"].insert_many(metric_docs)

    # 2. Ingest Incident via embedding and vector search
    clean_trace = embedding_service.normalize_text(scenario["error_message"], scenario["stack_trace"])
    embedding = await embedding_service.get_embedding(f"{scenario['error_message']}\n{clean_trace}")

    similar_incidents = await vector_search_service.find_similar_incidents(
        query_vector=embedding,
        top_k=3
    )

    top_match = similar_incidents[0] if similar_incidents else None
    
    # Match runbook
    matched_rb = None
    if top_match and top_match.get("runbook_id"):
        matched_rb = await db["runbooks"].find_one({"runbook_id": top_match["runbook_id"]}, {"_id": 0})
    if not matched_rb:
        matched_rb = await db["runbooks"].find_one({"service_name": service_name}, {"_id": 0})

    runbook_id = matched_rb.get("runbook_id") if matched_rb else None

    # AI Synthesis
    root_cause = await embedding_service.synthesize_root_cause(
        incident_data={"service_name": service_name, "error_message": scenario["error_message"], "normalized_stack_trace": clean_trace},
        matched_incident=top_match,
        runbook=matched_rb
    )

    incident_id = f"INC-CHAOS-{datetime.utcnow().strftime('%H%M%S')}"
    incident_doc = {
        "incident_id": incident_id,
        "title": scenario["title"],
        "service_name": service_name,
        "environment": scenario["environment"],
        "severity": "P1-Critical" if scenario["level"] in ["CRITICAL", "FATAL"] else "P2-High",
        "status": "ACTIVE",
        "error_message": scenario["error_message"],
        "normalized_stack_trace": clean_trace,
        "raw_stack_trace": scenario["stack_trace"],
        "source": "chaos-simulator",
        "git_metadata": scenario.get("git_metadata", {}),
        "embedding": embedding,
        "suggested_runbook_id": runbook_id,
        "top_matches": similar_incidents,
        "root_cause_summary": root_cause,
        "raw_payload": scenario,
        "created_at": now,
        "updated_at": now
    }

    await db["incidents"].insert_one(incident_doc)

    # Broadcast over WebSocket
    safe_broadcast = {k: v for k, v in incident_doc.items() if k not in ["_id", "embedding"]}
    safe_broadcast["created_at"] = now.isoformat()
    safe_broadcast["updated_at"] = now.isoformat()
    
    await ws_manager.broadcast("chaos_triggered", {
        "scenario": scenario["id"],
        "incident": safe_broadcast,
        "message": f"Simulated outage triggered: {scenario['title']}"
    })

    return {
        "status": "triggered",
        "scenario_id": scenario["id"],
        "incident_id": incident_id,
        "service_name": service_name,
        "deduplication_match": {
            "has_match": len(similar_incidents) > 0,
            "top_match_id": top_match["incident_id"] if top_match else None,
            "similarity_score": top_match["similarity_score"] if top_match else 0.0,
            "similarity_percentage": f"{int((top_match['similarity_score'] if top_match else 0) * 100)}%"
        },
        "matched_runbook": matched_rb.get("title") if matched_rb else None,
        "triage_url": f"/api/incidents/{incident_id}/triage"
    }
