import pytest
from app.services.embedding import embedding_service
from app.models.events import PolymorphicPayload

def test_stack_trace_normalization():
    raw_trace = """Traceback (most recent call last):
  File "checkout.py", line 184, in create_order
    session = await db.fetch_row(0x7ffd5e6b1234, token)
  Thread-4 PID: 12891 at 2026-11-18T10:12:44.123Z
ConnectionError: pool exhausted on port 5432"""

    cleaned = embedding_service.normalize_text("ConnectionError: pool exhausted", raw_trace)
    assert "0xMEM_ADDR" in cleaned
    assert "TIMESTAMP" in cleaned
    assert "THREAD_ID" in cleaned
    assert "ConnectionError: pool exhausted" in cleaned

@pytest.mark.asyncio
async def test_embedding_generation_fallback():
    vec = await embedding_service.get_embedding("PostgreSQL connection pool exhausted: timeout waiting for connection")
    assert isinstance(vec, list)
    assert len(vec) == 768
    # Verify vector is unit normalized
    import numpy as np
    norm = np.linalg.norm(vec)
    assert abs(norm - 1.0) < 1e-4

@pytest.mark.asyncio
async def test_semantic_similarity_deduplication():
    v1 = await embedding_service.get_embedding(
        "PostgreSQL connection pool exhausted: timeout waiting for connection (max_connections=100 exceeded)"
    )
    # Similar message with slight token changes
    v2 = await embedding_service.get_embedding(
        "PostgreSQL connection pool exhausted: timeout waiting for connection (max_connections=150 exceeded by pool 'auth')"
    )
    # Completely different error
    v3 = await embedding_service.get_embedding(
        "ModuleNotFoundError: No module named 'cryptography.hazmat.bindings._rust' during Docker container compilation"
    )

    import numpy as np
    sim_1_2 = float(np.dot(v1, v2))
    sim_1_3 = float(np.dot(v1, v3))

    assert sim_1_2 > 0.85, f"Expected high similarity for similar DB pool errors, got {sim_1_2}"
    assert sim_1_3 < 0.50, f"Expected low similarity for unrelated errors, got {sim_1_3}"
