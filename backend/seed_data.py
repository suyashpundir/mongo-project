import asyncio
import logging
from datetime import datetime, timedelta
from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection, db_manager
from app.services.embedding import embedding_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("netpulse.seed")

RUNBOOKS = [
    {
        "runbook_id": "RB-PG-POOL-EXHAUST",
        "title": "PostgreSQL Connection Pool Exhaustion Recovery",
        "error_signature": "PostgreSQL connection pool exhausted: timeout waiting for connection",
        "service_name": "checkout-api",
        "category": "DATABASE",
        "remediation_steps": [
            "Terminate stale idle connections holding pool handles in PostgreSQL.",
            "Increase max_connections and pool size in service configuration.",
            "Perform rolling restart of checkout-api worker pods.",
            "Verify endpoint response times and connection pool metrics."
        ],
        "remediation_commands": [
            "psql $DATABASE_URL -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < current_timestamp - INTERVAL '5 minutes';\"",
            "kubectl patch configmap/checkout-config -n production --type merge -p '{\"data\":{\"DB_POOL_MAX\":\"250\"}}'",
            "kubectl rollout restart deployment/checkout-api -n production",
            "curl -sf http://checkout-api.internal/healthz | jq ."
        ],
        "rollback_script": "kubectl rollout undo deployment/checkout-api -n production",
        "post_mortem_notes": "Root cause was parallel asynchronous tasks acquiring DB connections without releasing them on unhandled timeout exceptions. Pool size expanded and connection leak guard implemented.",
        "verification_check": "curl -sf http://checkout-api.internal/healthz",
        "success_rate": 0.98,
        "average_recovery_time_sec": 95,
        "created_at": datetime.utcnow() - timedelta(days=45)
    },
    {
        "runbook_id": "RB-CI-RUST-COMPILATION",
        "title": "CI/CD Alpine Docker Missing Rust Compiler Fix",
        "error_signature": "ModuleNotFoundError: No module named 'cryptography.hazmat.bindings._rust'",
        "service_name": "ci-cd-builder",
        "category": "CI_BUILD",
        "remediation_steps": [
            "Pin cryptography to 41.0.7 in requirements.txt to avoid uncompiled Rust wheel compilation on alpine-slim.",
            "Invalidate remote Docker layer build cache on GitHub Actions.",
            "Trigger automated CI rebuild on patch branch."
        ],
        "remediation_commands": [
            "sed -i 's/cryptography>=42.0.0/cryptography==41.0.7/g' backend/requirements.txt",
            "git commit -am 'fix(deps): pin cryptography==41.0.7 for alpine wheel compatibility' && git push origin main",
            "gh workflow run ci.yml --ref main"
        ],
        "rollback_script": "git revert HEAD --no-edit && git push origin main",
        "post_mortem_notes": "Dependabot bumped cryptography to v42 without Rust compiler toolchain present in Alpine Docker base. Pinned version while migrating Dockerfile to multi-stage Rust build.",
        "verification_check": "gh run list --workflow=ci.yml --limit 1",
        "success_rate": 0.99,
        "average_recovery_time_sec": 140,
        "created_at": datetime.utcnow() - timedelta(days=30)
    },
    {
        "runbook_id": "RB-K8S-OOM-KILL",
        "title": "Kubernetes Pod OOMKilled & Cascading Retry Remediation",
        "error_signature": "Kubernetes Pod OOMKilled: container 'payment-worker' exceeded memory limit (2048Mi)",
        "service_name": "payment-gateway",
        "category": "MEMORY_LEAK",
        "remediation_steps": [
            "Revert unconstrained memory cache commit in payment idempotency service.",
            "Scale pod memory limits from 2048Mi to 3072Mi to absorb backpressure.",
            "Reset payment circuit breakers on upstream checkout-api."
        ],
        "remediation_commands": [
            "kubectl set resources deployment payment-gateway --limits=memory=3072Mi,cpu=2000m -n production",
            "kubectl rollout restart deployment/payment-gateway -n production",
            "curl -X POST http://checkout-api.internal/admin/circuit-breakers/reset"
        ],
        "rollback_script": "kubectl rollout undo deployment/payment-gateway -n production",
        "post_mortem_notes": "In-memory idempotency token dictionary lacked TTL eviction, causing linear RSS memory growth under sustained load until cgroup OOM killed the pod.",
        "verification_check": "kubectl get pods -l app=payment-gateway -n production",
        "success_rate": 0.94,
        "average_recovery_time_sec": 110,
        "created_at": datetime.utcnow() - timedelta(days=14)
    },
    {
        "runbook_id": "RB-REDIS-NOEVICTION",
        "title": "Redis Memory Saturation & Eviction Policy Remediation",
        "error_signature": "RedisConnectionError: OOM command not allowed when used memory > 'maxmemory'",
        "service_name": "auth-service",
        "category": "NETWORK",
        "remediation_steps": [
            "Dynamically switch Redis eviction policy from noeviction to allkeys-lru.",
            "Purge volatile expired auth tokens from memory.",
            "Verify memory usage returns below 70% threshold."
        ],
        "remediation_commands": [
            "redis-cli -h redis-cluster-master CONFIG SET maxmemory-policy allkeys-lru",
            "redis-cli -h redis-cluster-master CONFIG REWRITE",
            "redis-cli -h redis-cluster-master MEMORY PURGE",
            "redis-cli -h redis-cluster-master INFO memory | grep used_memory_human"
        ],
        "rollback_script": "redis-cli -h redis-cluster-master CONFIG SET maxmemory-policy volatile-lru",
        "post_mortem_notes": "Misconfigured Redis configmap had maxmemory-policy set to noeviction, rejecting all session write commands once 1GB RAM ceiling was reached.",
        "verification_check": "redis-cli -h redis-cluster-master PING",
        "success_rate": 0.97,
        "average_recovery_time_sec": 45,
        "created_at": datetime.utcnow() - timedelta(days=21)
    }
]

HISTORICAL_INCIDENTS = [
    {
        "incident_id": "INC-2026-0104",
        "title": "checkout-api: PostgreSQL connection pool exhausted under surge traffic",
        "service_name": "checkout-api",
        "environment": "production",
        "severity": "P1-Critical",
        "status": "RESOLVED",
        "error_message": "PostgreSQL connection pool exhausted: timeout waiting for connection (max_connections=100 exceeded by pool 'auth-checkout')",
        "normalized_stack_trace": "asyncpg.exceptions.TooManyConnectionsError: PostgreSQL connection pool exhausted: timeout waiting for connection\nFile checkout.py line 184 in create_order\nFile asyncpg/pool.py line 402 in acquire",
        "raw_stack_trace": "asyncpg.exceptions.TooManyConnectionsError: PostgreSQL connection pool exhausted: timeout waiting for connection (max_connections=100 exceeded by pool 'auth-checkout')",
        "source": "kubernetes-k8s",
        "git_metadata": {
            "commit_hash": "62bf190",
            "branch": "main",
            "author": "sre-team@company.com",
            "commit_message": "perf(checkout): parallelize database queries",
            "diff_summary": "+++ b/services/checkout.py\n+ await asyncio.gather(*queries)"
        },
        "suggested_runbook_id": "RB-PG-POOL-EXHAUST",
        "root_cause_summary": "Database connection pool starvation on checkout-api due to unmanaged parallel queries without connection pool limits. Resolved via pool expansion and connection drain.",
        "created_at": datetime.utcnow() - timedelta(days=12)
    },
    {
        "incident_id": "INC-2026-0089",
        "title": "ci-cd-builder: Rust compiler missing in Alpine Docker container during cryptography build",
        "service_name": "ci-cd-builder",
        "environment": "production",
        "severity": "P2-High",
        "status": "RESOLVED",
        "error_message": "CI Build Failure: ModuleNotFoundError: No module named 'cryptography.hazmat.bindings._rust' during Docker container compilation",
        "normalized_stack_trace": "ModuleNotFoundError: No module named 'cryptography.hazmat.bindings._rust'\nerror: Rust compiler 'cargo' not found in alpine-slim container\nGitHub Actions Job 'build-and-deploy' terminated with exit code 1",
        "raw_stack_trace": "ModuleNotFoundError: No module named 'cryptography.hazmat.bindings._rust'",
        "source": "github-actions",
        "git_metadata": {
            "commit_hash": "4a98e21",
            "branch": "main",
            "author": "dependabot[bot]",
            "commit_message": "chore(deps): update cryptography to 42.0.0",
            "diff_summary": "+++ b/requirements.txt\n-cryptography==41.0.7\n+cryptography>=42.0.0"
        },
        "suggested_runbook_id": "RB-CI-RUST-COMPILATION",
        "root_cause_summary": "Alpine Docker base image lacked Cargo/Rust toolchain required to compile cryptography wheel. Resolved by pinning cryptography==41.0.7.",
        "created_at": datetime.utcnow() - timedelta(days=20)
    },
    {
        "incident_id": "INC-2026-0062",
        "title": "payment-gateway: Pod OOMKilled (Exit Code 137) during flash sale",
        "service_name": "payment-gateway",
        "environment": "production",
        "severity": "P1-Critical",
        "status": "RESOLVED",
        "error_message": "Kubernetes Pod OOMKilled: container 'payment-worker' exceeded memory limit (2048Mi) and was terminated with exit code 137",
        "normalized_stack_trace": "Memory cgroup out of memory: Killed process payment-worker (python) total-vm:2841024kB, anon-rss:2088960kB\ncontainer payment-worker in pod payment-gateway OOMKilled\nupstream-caller: checkout-api received HTTP 504 Gateway Timeout",
        "raw_stack_trace": "Kubernetes Pod OOMKilled: container 'payment-worker' exceeded memory limit (2048Mi)",
        "source": "kubernetes-k8s",
        "git_metadata": {
            "commit_hash": "e12f980",
            "branch": "main",
            "author": "payment-team@company.com",
            "commit_message": "fix(cache): in-memory cache without TTL",
            "diff_summary": "+++ b/payment/cache.py\n+ cache[token] = payload"
        },
        "suggested_runbook_id": "RB-K8S-OOM-KILL",
        "root_cause_summary": "Unbounded memory growth in payment token cache triggered cgroup OOM termination. Resolved by bumping memory limits and reverting cache commit.",
        "created_at": datetime.utcnow() - timedelta(days=28)
    },
    {
        "incident_id": "INC-2026-0041",
        "title": "auth-service: Redis OOM command not allowed maxmemory exhaustion",
        "service_name": "auth-service",
        "environment": "production",
        "severity": "P2-High",
        "status": "RESOLVED",
        "error_message": "RedisConnectionError: OOM command not allowed when used memory > 'maxmemory' (maxmemory_policy=noeviction)",
        "normalized_stack_trace": "redis.exceptions.ResponseError: OOM command not allowed when used memory > 'maxmemory'\nFile session.py line 89 in store_jwt_session\nRedis node at redis-cluster-master:6379 rejecting writes",
        "raw_stack_trace": "RedisConnectionError: OOM command not allowed when used memory > 'maxmemory'",
        "source": "service-mesh",
        "git_metadata": {
            "commit_hash": "771ca81",
            "branch": "main",
            "author": "infra-team@company.com",
            "commit_message": "chore(redis): set policy to noeviction",
            "diff_summary": "+++ b/k8s/redis.yaml\n-maxmemory-policy allkeys-lru\n+maxmemory-policy noeviction"
        },
        "suggested_runbook_id": "RB-REDIS-NOEVICTION",
        "root_cause_summary": "Redis reached memory limit with noeviction policy, causing auth service write failures. Resolved by setting policy to allkeys-lru.",
        "created_at": datetime.utcnow() - timedelta(days=35)
    }
]

async def seed_database():
    logger.info("Connecting to MongoDB to seed initial NetPulse data...")
    await connect_to_mongo()
    db = db_manager.db
    if db is None:
        logger.error("Database connection failed. Cannot seed data.")
        return

    # 1. Seed Runbooks
    logger.info("Seeding verified runbooks...")
    for rb in RUNBOOKS:
        await db["runbooks"].update_one(
            {"runbook_id": rb["runbook_id"]},
            {"$set": rb},
            upsert=True
        )
    logger.info(f"Seeded {len(RUNBOOKS)} runbooks successfully.")

    # 2. Seed Historical Incidents with Embeddings
    logger.info("Generating embeddings and seeding historical incidents...")
    for inc in HISTORICAL_INCIDENTS:
        text_for_embed = f"{inc['error_message']}\n{inc['normalized_stack_trace']}"
        embedding = await embedding_service.get_embedding(text_for_embed)
        inc["embedding"] = embedding
        inc["updated_at"] = inc["created_at"]
        inc["top_matches"] = []
        inc["upstream_services"] = ["api-gateway"]
        inc["downstream_services"] = ["payment-gateway", "postgres-orders"]
        inc["blast_radius_score"] = 0.65
        inc["raw_payload"] = {
            "source": inc["source"],
            "error": inc["error_message"],
            "git": inc["git_metadata"]
        }

        await db["incidents"].update_one(
            {"incident_id": inc["incident_id"]},
            {"$set": inc},
            upsert=True
        )
    logger.info(f"Seeded {len(HISTORICAL_INCIDENTS)} historical incidents with 768-dim embeddings.")

    # 3. Seed Baseline Metrics for Time Series
    logger.info("Seeding baseline telemetry metrics into 'raw_events'...")
    now = datetime.utcnow()
    services = ["api-gateway", "checkout-api", "auth-service", "payment-gateway", "inventory-service"]
    metric_docs = []

    for svc in services:
        for min_ago in range(30, 0, -2):
            ts = now - timedelta(minutes=min_ago)
            metric_docs.append({
                "service_name": svc,
                "timestamp": ts,
                "metric_type": "cpu_percent",
                "value": round(25.0 + (min_ago % 7) * 2.5, 1),
                "metadata": {"source": "seed-heartbeat"}
            })
            metric_docs.append({
                "service_name": svc,
                "timestamp": ts,
                "metric_type": "memory_mb",
                "value": round(450.0 + (min_ago % 5) * 15.0, 1),
                "metadata": {"source": "seed-heartbeat"}
            })
            metric_docs.append({
                "service_name": svc,
                "timestamp": ts,
                "metric_type": "latency_ms",
                "value": round(35.0 + (min_ago % 4) * 8.0, 1),
                "metadata": {"source": "seed-heartbeat"}
            })
            metric_docs.append({
                "service_name": svc,
                "timestamp": ts,
                "metric_type": "error_rate",
                "value": 0.01,
                "metadata": {"source": "seed-heartbeat"}
            })

    if metric_docs:
        await db["raw_events"].insert_many(metric_docs)
        logger.info(f"Seeded {len(metric_docs)} time-series metric data points into 'raw_events'.")

    logger.info("NetPulse database seeding completed successfully!")
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(seed_database())
