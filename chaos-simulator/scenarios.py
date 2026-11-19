CHAOS_SCENARIOS = {
    "db_pool_exhaustion": {
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
        "metrics": {"cpu_percent": 96.5, "memory_mb": 820.0, "latency_ms": 3200.0, "error_rate": 44.0}
    },
    "bad_ci_dependency": {
        "service_name": "ci-cd-builder",
        "environment": "production",
        "level": "FATAL",
        "error_message": "CI Build Failure: ModuleNotFoundError: No module named 'cryptography.hazmat.bindings._rust' during Docker container compilation",
        "stack_trace": """Step 8/14 : RUN pip install -r requirements.txt
Collecting cryptography>=42.0.0 (from -r requirements.txt (line 14))
  Installing build dependencies ... done
  Getting requirements to build wheel ... error
  fatal error: Rust compiler 'cargo' not found in alpine-slim container
  ModuleNotFoundError: No module named 'cryptography.hazmat.bindings._rust'
The command '/bin/sh -c pip install -r requirements.txt' returned a non-zero code: 1""",
        "git_metadata": {
            "commit_hash": "c71e04b",
            "branch": "main",
            "author": "dependabot[bot]",
            "commit_message": "build(deps): bump cryptography from 41.0.7 to 42.0.5 in backend",
            "diff_summary": "+++ b/backend/requirements.txt\n@@ -14,1 +14,1 @@\n-cryptography==41.0.7\n+cryptography>=42.0.0"
        },
        "metrics": {"cpu_percent": 98.0, "memory_mb": 890.0, "latency_ms": 120.0, "error_rate": 100.0}
    },
    "memory_leak_oom": {
        "service_name": "payment-gateway",
        "environment": "production",
        "level": "CRITICAL",
        "error_message": "Kubernetes Pod OOMKilled: container 'payment-worker' exceeded memory limit (2048Mi) and was terminated with exit code 137",
        "stack_trace": """Kubelet log: node-worker-pool-3 kernel: Memory cgroup out of memory: Killed process 38192 (python) total-vm:2841024kB, anon-rss:2088960kB
container payment-worker in pod payment-gateway-7b9c6f849d-v9x2l OOMKilled
upstream-caller: checkout-api received HTTP 504 Gateway Timeout""",
        "git_metadata": {
            "commit_hash": "e12f980",
            "branch": "main",
            "author": "payment-team@company.com",
            "commit_message": "fix(cache): cache idempotency tokens in memory without LRU eviction TTL",
            "diff_summary": "+++ b/services/payment/idempotency.py\n@@ -42,3 +42,3 @@\n- cache = ExpiringLRUDict(ttl_seconds=3600)\n+ cache = {}\n+ cache[token] = payload"
        },
        "metrics": {"cpu_percent": 99.0, "memory_mb": 2048.0, "latency_ms": 4800.0, "error_rate": 52.0}
    }
}
