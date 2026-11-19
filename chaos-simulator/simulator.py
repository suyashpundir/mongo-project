import os
import time
import random
import logging
import argparse
import httpx
from scenarios import CHAOS_SCENARIOS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [ChaosSim]: %(message)s")
logger = logging.getLogger("ChaosSimulator")

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

def send_telemetry_heartbeat(client: httpx.Client, service_name: str):
    """Sends baseline healthy telemetry to populate raw_events."""
    payload = {
        "source": "chaos-telemetry-daemon",
        "service_name": service_name,
        "environment": "production",
        "level": "INFO",
        "metrics": {
            "cpu_percent": round(random.uniform(20.0, 45.0), 1),
            "memory_mb": round(random.uniform(400.0, 600.0), 1),
            "latency_ms": round(random.uniform(25.0, 60.0), 1),
            "error_rate": round(random.uniform(0.0, 0.05), 3),
        }
    }
    try:
        res = client.post(f"{BACKEND_URL}/api/webhook/ingest", json=payload, timeout=5.0)
        logger.debug(f"Telemetry sent for {service_name}: {res.status_code}")
    except Exception as e:
        logger.debug(f"Telemetry heartbeat failed: {e}")

def trigger_chaos_outage(client: httpx.Client, scenario_key: str):
    """Triggers an outage scenario via backend chaos API."""
    logger.info(f"Triggering Chaos Outage: {scenario_key}...")
    try:
        res = client.post(
            f"{BACKEND_URL}/api/chaos/trigger",
            json={"scenario": scenario_key},
            timeout=10.0
        )
        if res.status_code == 200:
            data = res.json()
            logger.info(f"Outage successfully created! Incident: {data.get('incident_id')} (Deduplication match: {data.get('deduplication_match', {}).get('similarity_percentage')})")
        else:
            logger.error(f"Failed to trigger chaos: {res.status_code} - {res.text}")
    except Exception as e:
        logger.error(f"Error connecting to backend: {e}")

def main():
    parser = argparse.ArgumentParser(description="NetPulse Chaos Engineering Simulator")
    parser.add_argument("--scenario", choices=list(CHAOS_SCENARIOS.keys()), help="Single scenario to trigger")
    parser.add_argument("--daemon", action="store_true", help="Run indefinitely emitting background telemetry and occasional chaos")
    parser.add_argument("--interval", type=int, default=10, help="Interval in seconds for telemetry daemon")
    parser.add_argument("--target", default=BACKEND_URL, help="Backend URL target")
    args = parser.parse_args()

    client = httpx.Client(base_url=args.target)
    services = ["api-gateway", "checkout-api", "auth-service", "payment-gateway", "inventory-service"]

    if args.scenario:
        trigger_chaos_outage(client, args.scenario)
        return

    logger.info(f"Chaos Simulator running in daemon mode against {args.target}")
    iteration = 0
    try:
        while True:
            # Emit telemetry for each service
            for svc in services:
                send_telemetry_heartbeat(client, svc)

            iteration += 1
            # Every 12 iterations (approx 2 minutes), trigger a random chaos scenario if in daemon mode
            if args.daemon and iteration % 12 == 0:
                chosen = random.choice(list(CHAOS_SCENARIOS.keys()))
                trigger_chaos_outage(client, chosen)

            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Chaos Simulator stopped.")

if __name__ == "__main__":
    main()
