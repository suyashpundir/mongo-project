import pytest
from datetime import datetime
from app.services.aggregation import aggregation_service

@pytest.mark.asyncio
async def test_pre_crash_curve_synthesis():
    now = datetime.utcnow()
    points = aggregation_service._synthesize_pre_crash_curve("checkout-api", now, window_minutes=15)
    
    assert len(points) > 10
    # Earliest points should have low CPU
    assert points[0].cpu_percent < 45.0
    # Peak points near crash should have elevated latency / CPU
    peak_point = points[-1]
    assert peak_point.cpu_percent > 80.0
    assert peak_point.latency_ms > 400.0

    # Ensure deployment marker exists
    deployment_points = [p for p in points if p.is_deployment_marker]
    assert len(deployment_points) == 1
    assert "Deployed commit" in deployment_points[0].deployment_info

@pytest.mark.asyncio
async def test_service_topology_graph():
    topo = await aggregation_service.get_service_topology(active_service="checkout-api")
    assert "nodes" in topo
    assert "edges" in topo
    assert topo["root_failure_node"] == "checkout-api"
    
    # checkout-api should be CRITICAL
    checkout_node = next(n for n in topo["nodes"] if n["id"] == "checkout-api")
    assert checkout_node["status"] == "CRITICAL"
    
    # payment-gateway (downstream) should be DEGRADED
    payment_node = next(n for n in topo["nodes"] if n["id"] == "payment-gateway")
    assert payment_node["status"] == "DEGRADED"
