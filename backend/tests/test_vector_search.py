import pytest
from app.services.vector_search import vector_search_service
from app.services.embedding import embedding_service
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_local_cosine_search_fallback():
    # Setup dummy candidate docs
    v1 = await embedding_service.get_embedding("Database connection timeout")
    v2 = await embedding_service.get_embedding("Memory cgroup killed worker")
    
    mock_candidates = [
        {
            "incident_id": "INC-TEST-1",
            "title": "DB Timeout",
            "service_name": "checkout-api",
            "severity": "P1-Critical",
            "status": "RESOLVED",
            "error_message": "Database connection timeout",
            "created_at": "2026-11-18T10:00:00Z",
            "suggested_runbook_id": "RB-PG-POOL-EXHAUST",
            "embedding": v1
        },
        {
            "incident_id": "INC-TEST-2",
            "title": "OOM Killed",
            "service_name": "payment-gateway",
            "severity": "P1-Critical",
            "status": "RESOLVED",
            "error_message": "Memory cgroup killed worker",
            "created_at": "2026-11-18T10:00:00Z",
            "suggested_runbook_id": "RB-K8S-OOM-KILL",
            "embedding": v2
        }
    ]

    with patch("app.services.vector_search.db_manager") as mock_db_manager:
        mock_db = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = mock_candidates
        mock_db["incidents"].find.return_value.sort.return_value.limit.return_value = mock_cursor
        mock_db_manager.db = mock_db
        mock_db_manager.is_atlas_vector_search_ready = False

        query_vec = await embedding_service.get_embedding("Database connection pool timeout occurred")
        results = await vector_search_service.find_similar_incidents(query_vec, top_k=2)

        assert len(results) > 0
        assert results[0]["incident_id"] == "INC-TEST-1"
        assert results[0]["similarity_score"] > 0.70
