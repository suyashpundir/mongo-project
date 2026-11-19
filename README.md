# ⚡ NetPulse — Autonomous SRE & Self-Healing Incident Triage Platform

> An autonomous, self-healing infrastructure and CI/CD incident-triage and root-cause analysis platform. Ingests polymorphic logs and telemetry, performs semantic stack-trace deduplication via **MongoDB Atlas Vector Search**, reconstructs causal blast-radius timelines via **MongoDB Aggregation Pipelines**, and surfaces verified fixes in a real-time dark-mode command center.

---

## 🏛️ System Architecture

```
                                  [ POLYMORPHIC INGESTION ]
                                             │
      ┌───────────────────────┬──────────────┴────────────────┬──────────────────────┐
      │                       │                               │                      │
GitHub / GitLab CI      Docker Daemon                  Kubernetes K8s        CloudWatch / Metrics
      │                       │                               │                      │
      └───────────────────────┼───────────────────────────────┴──────────────────────┘
                              ▼
                  POST /api/webhook/ingest
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
       [ High-Frequency ]            [ Crash Events & ]
       [ Telemetry Stream ]          [ Stack Traces   ]
               │                             │
               ▼                             ▼
        MongoDB Atlas               768-Dim Semantic Embedding
       Time Series Coll.           (Gemini text-embedding-004
        (`raw_events`)               or deterministic fallback)
               │                             │
               │                             ▼
               │                    MongoDB Atlas Search
               │                      $vectorSearch
               │               (Top 3 Similar Past Outages)
               │                             │
               └──────────────┬──────────────┘
                              ▼
                 MongoDB Aggregation Pipeline
               ($match, $group, $lookup, $sort)
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
Pre-Crash Metric      Causal Blast Radius     Verified Runbook
Spike Timeline (15m)    Dependency Graph     Remediation Commands
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                    FastAPI WebSocket & SSE
                              │
                              ▼
          [ NetPulse Dark-Mode Command Center UI ]
                 (React + Vite + Recharts)
```

---

## ✨ Key Features

1. **Polymorphic Telemetry & Crash Ingestion:**
   - Ingests arbitrary nested JSON payloads from GitHub Actions build logs, Docker crash dumps, Kubernetes OOMKilled events, and service mesh heartbeats.
   - Normalizes timestamps, sanitizes transient memory pointers (`0x7ffd...`) and thread IDs, and routes metrics to MongoDB Time Series collections while preserving the raw dynamic payload.

2. **Semantic Stack-Trace Deduplication (Atlas Vector Search):**
   - Projects normalized error signatures and traces onto a **768-dimensional vector space** using Google Gemini API (`text-embedding-004`) with an offline-capable high-precision semantic fallback.
   - Executes MongoDB Atlas `$vectorSearch` with cosine distance to deduplicate incoming crashes against historical outages (e.g. *"94% match to Incident #INC-2026-0104"*).

3. **Causal Blast-Radius Timeline (MongoDB Aggregation Pipeline):**
   - Runs high-performance aggregation pipelines (`$match`, `$group`/`$dateTrunc`, `$lookup`, `$sort`) across `raw_events`, `incidents`, and `runbooks`.
   - Reconstructs the exact 15-minute pre-crash escalation curve (CPU, memory, latency surges, and error spikes) overlaid with git deployment markers.

4. **Self-Healing Runbook Execution:**
   - Automatically matches error signatures to verified remediation commands and rollback scripts.
   - Provides one-click autonomous self-healing execution with real-time terminal streaming over WebSockets.

5. **Integrated Chaos Engineering Simulator:**
   - Built-in multi-scenario chaos simulator microservice to trigger realistic cascading outages on demand:
     - **DB Connection Pool Exhaustion:** `checkout-api` pool starvation cascading to `auth-service` timeouts and 502s.
     - **Bad CI Dependency Bump:** Alpine Docker missing Rust compiler (`cryptography` build failure).
     - **Memory Leak / K8s OOMKilled:** Cgroup exit code 137 pod termination triggering payment gateway retry storms.
     - **Redis Cache Eviction Storm:** Redis `noeviction` OOM flooding PostgreSQL auth queries.

6. **Production-Ready CI/CD & Vercel Deployment:**
   - Pre-configured for **Vercel** with SPA rewrites (`vercel.json`).
   - GitHub Actions pipelines for automated pytest linting, TypeScript verification, Docker build validation, and Vercel Preview/Production deployments.

---

## 🚀 Quickstart Guide

### 1. Start with Docker Compose
```bash
# 1. Clone repository & configure env
cp .env.example .env

# 2. Spin up MongoDB, FastAPI Backend, React Frontend & Chaos Simulator
docker-compose up --build
```

### 2. Seed Initial Historical Incidents & Runbooks
In a separate terminal:
```bash
docker exec -it netpulse-backend python seed_data.py
```

### 3. Open the Command Center
- **Frontend Dashboard:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Interactive Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📁 Repository Structure

```
netpulse/
├── backend/
│   ├── app/
│   │   ├── models/          # Pydantic v2 schemas (Incident, Runbook, Telemetry)
│   │   ├── routes/          # Webhook ingestion, triage, chaos, runbooks, topology
│   │   ├── services/        # Vector search, embeddings, aggregation pipelines, WS
│   │   ├── config.py        # Settings and environment bindings
│   │   ├── database.py      # Motor async MongoDB client & time-series setup
│   │   └── main.py          # FastAPI application & WebSocket handlers
│   ├── tests/               # Pytest suite (ingestion, vector search, aggregation, chaos)
│   ├── atlas_vector_index.json # MongoDB Atlas Vector Search index definition
│   ├── seed_data.py         # Historical incidents and runbook seeder
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/      # Header, IncidentFeed, TopologyMap, Timeline, DiffView
│   │   ├── services/        # API client & real-time WebSocket manager
│   │   ├── types/           # Strict TypeScript interfaces
│   │   ├── App.tsx          # Master command center view
│   │   └── main.tsx
│   ├── vercel.json          # Vercel deployment & rewrite configuration
│   ├── nginx.conf           # Docker production container server
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── chaos-simulator/
│   ├── simulator.py         # Autonomous chaos daemon and CLI trigger
│   ├── scenarios.py         # Multi-service cascading outage definitions
│   ├── requirements.txt
│   └── Dockerfile
├── .github/workflows/
│   ├── ci.yml               # Backend pytest, frontend build, docker verify
│   └── deploy-vercel.yml    # Vercel CLI preview & prod deployment
├── docker-compose.yml
├── DEPLOYMENT.md
└── README.md
```

---

## 🧪 Testing

Run backend unit and integration tests:
```bash
cd backend
pytest tests/ -v
```

Run frontend TypeScript verification and build:
```bash
cd frontend
npm run build
```

---

## 📄 License
MIT License. Built for modern autonomous cloud infrastructure and DevOps teams.
