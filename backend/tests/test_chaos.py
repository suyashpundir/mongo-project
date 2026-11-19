import pytest
from app.routes.chaos import CHAOS_SCENARIOS

def test_chaos_scenarios_definitions():
    assert "db_pool_exhaustion" in CHAOS_SCENARIOS
    assert "bad_ci_dependency" in CHAOS_SCENARIOS
    assert "memory_leak_oom" in CHAOS_SCENARIOS
    assert "cache_partition" in CHAOS_SCENARIOS

    for scenario_id, data in CHAOS_SCENARIOS.items():
        assert "service_name" in data
        assert "error_message" in data
        assert "stack_trace" in data
        assert "metrics_ramp" in data
        assert len(data["metrics_ramp"]) >= 3
