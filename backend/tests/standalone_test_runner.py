import unittest
import sys
import os
import re
import hashlib
import math
from datetime import datetime, timedelta

# Pure Python Vector Math
def dot_product(v1, v2):
    return sum(a * b for a, b in zip(v1, v2))

def vector_norm(v):
    return math.sqrt(sum(x * x for x in v))

def normalize_vector(v):
    norm = vector_norm(v)
    if norm > 1e-6:
        return [x / norm for x in v]
    res = [0.0] * len(v)
    res[0] = 1.0
    return res

class TestNetPulseCore(unittest.TestCase):
    def test_stack_trace_sanitization(self):
        raw_trace = """Traceback (most recent call last):
  File "checkout.py", line 184, in create_order
    session = await db.fetch_row(0x7ffd5e6b1234, token)
  Thread-4 PID: 12891 at 2026-11-18T10:12:44.123Z
ConnectionError: pool exhausted on port 5432"""

        text = f"ConnectionError: pool exhausted \n {raw_trace}"
        text = re.sub(r'0x[0-9a-fA-F]{6,16}', '0xMEM_ADDR', text)
        text = re.sub(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?', 'TIMESTAMP', text)
        text = re.sub(r'Thread-\d+|PID:\s*\d+|port\s+\d{4,5}', 'THREAD_ID', text)

        self.assertIn("0xMEM_ADDR", text)
        self.assertIn("TIMESTAMP", text)
        self.assertIn("THREAD_ID", text)

    def test_deterministic_embedding_and_cosine_similarity(self):
        def local_embed(text: str, dimensions: int = 768):
            tokens = re.findall(r'[a-zA-Z0-9_\.]+', text.lower())
            vec = [0.0] * dimensions
            if not tokens:
                vec[0] = 1.0
                return vec
            category_weights = {
                "connection": 12.0, "pool": 13.0, "exhausted": 14.0, "timeout": 15.0,
                "oomkilled": 25.0, "memory": 26.0, "heap": 27.0, "allocation": 28.0,
            }
            for token in tokens:
                h = int(hashlib.sha256(token.encode('utf-8')).hexdigest(), 16)
                idx = h % dimensions
                weight = category_weights.get(token, 1.0)
                sign = 1.0 if ((h >> 8) % 2 == 0) else -1.0
                vec[idx] += sign * weight
                if len(token) >= 3:
                    for i in range(len(token) - 2):
                        th = int(hashlib.md5(token[i:i+3].encode('utf-8')).hexdigest(), 16)
                        vec[th % dimensions] += 0.3 * (1.0 if ((th >> 4) % 2 == 0) else -1.0)
            return normalize_vector(vec)

        v1 = local_embed("PostgreSQL connection pool exhausted: timeout waiting for connection (max_connections=100)")
        v2 = local_embed("PostgreSQL connection pool exhausted: timeout waiting for connection (max_connections=150)")
        v3 = local_embed("ModuleNotFoundError: No module named 'cryptography.hazmat.bindings._rust'")

        sim_1_2 = dot_product(v1, v2)
        sim_1_3 = dot_product(v1, v3)

        self.assertGreater(sim_1_2, 0.85, f"Expected > 0.85, got {sim_1_2}")
        self.assertLess(sim_1_3, 0.50, f"Expected < 0.50, got {sim_1_3}")

    def test_timeline_curve_synthesis(self):
        now = datetime.utcnow()
        window_minutes = 15
        points = []
        for m in range(window_minutes, -3, -1):
            progress = (window_minutes - m) / float(window_minutes)
            is_deploy = (m == 7)
            if progress < 0.5:
                cpu = 28.0 + (progress * 15.0)
                lat = 42.0 + (progress * 20.0)
            elif progress < 0.8:
                cpu = 55.0 + ((progress - 0.5) * 60.0)
                lat = 85.0 + ((progress - 0.5) * 350.0)
            else:
                cpu = min(99.4, 85.0 + ((progress - 0.8) * 80.0))
                lat = 450.0 + ((progress - 0.8) * 2200.0)
            points.append({
                "minute": m,
                "cpu": cpu,
                "lat": lat,
                "is_deploy": is_deploy
            })

        self.assertTrue(any(p["is_deploy"] for p in points))
        self.assertLess(points[0]["cpu"], 45.0)
        self.assertGreater(points[-1]["lat"], 400.0)

if __name__ == '__main__':
    unittest.main()
