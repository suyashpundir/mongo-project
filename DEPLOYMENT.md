# NetPulse — Production & Local Deployment Guide

This guide covers local environment execution using Docker Compose, MongoDB Atlas Vector Search index creation, and CI/CD deployment to Vercel and production backends.

---

## 1. Quickstart with Docker Compose (Local Dev & Demo)

NetPulse runs completely out of the box with zero external accounts or credentials required. A local MongoDB container, the FastAPI backend, the React dark-mode dashboard, and the Chaos Simulator are orchestrated via Docker Compose.

### Step 1: Clone & Configure Environment
```bash
cp .env.example .env
```
*(Optional)* Add your Google Gemini API key to `.env` for generative root-cause analysis:
```env
GEMINI_API_KEY=AIzaSy...
```
*Note: If no API key is provided, NetPulse automatically falls back to its deterministic 768-dimensional semantic embedding and diagnosis engine.*

### Step 2: Start All Services
```bash
docker-compose up --build
```

### Step 3: Access Services
- **React Command Center Dashboard:** [http://localhost:3000](http://localhost:3000)
- **FastAPI OpenAPI Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **MongoDB Instance:** `mongodb://localhost:27017`

### Step 4: Seed Initial Historical Incidents & Runbooks
In a separate terminal, seed the database with realistic historical outages:
```bash
docker exec -it netpulse-backend python seed_data.py
```
This populates:
1. Verified Runbooks (`RB-PG-POOL-EXHAUST`, `RB-CI-RUST-COMPILATION`, `RB-K8S-OOM-KILL`, `RB-REDIS-NOEVICTION`).
2. Historical Incidents with unit-normalized 768-dim embeddings.
3. 30 minutes of baseline time-series telemetry metrics in `raw_events`.

---

## 2. MongoDB Atlas Vector Search Setup

To enable managed cloud vector search rather than the local cosine fallback:

### Step 1: Create a MongoDB Atlas Cluster (M0 Free Tier or higher)
1. Log in to [MongoDB Atlas](https://cloud.mongodb.com).
2. Create a Database named `netpulse`.
3. Obtain your connection string:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
4. Set `MONGODB_URI` in your `.env` or deployment secrets.

### Step 2: Create the Vector Search Index (`vector_index`)
1. In the Atlas UI, navigate to **Atlas Search** > **Create Index**.
2. Select **JSON Editor** and choose the `incidents` collection in the `netpulse` database.
3. Name the index `vector_index`.
4. Paste the JSON definition from `backend/atlas_vector_index.json`:
```json
{
  "name": "vector_index",
  "type": "vectorSearch",
  "definition": {
    "fields": [
      {
        "type": "vector",
        "path": "embedding",
        "numDimensions": 768,
        "similarity": "cosine"
      },
      {
        "type": "filter",
        "path": "service_name"
      },
      {
        "type": "filter",
        "path": "environment"
      },
      {
        "type": "filter",
        "path": "status"
      }
    ]
  }
}
```
5. Click **Create Search Index**. Once indexing is ready (usually < 1 minute), NetPulse automatically activates native Atlas `$vectorSearch`.

---

## 3. Frontend Vercel Deployment

The `/frontend` application is built with Vite + React + TypeScript and is pre-configured for Vercel deployment with client-side SPA rewrites.

### Manual Vercel Deployment via CLI
```bash
cd frontend
npm install -g vercel
vercel login
vercel link
vercel --prod
```

### Automated CI/CD Deployment via GitHub Actions
NetPulse includes `.github/workflows/deploy-vercel.yml` which automatically:
- Runs full CI tests on pull requests.
- Creates ephemeral Vercel Preview Deployments and comments the URL on PRs.
- Deploys directly to Production when PRs merge to `main`.

### Required GitHub Repository Secrets
Navigate to **Settings** > **Secrets and variables** > **Actions** in GitHub:

| Secret Name | Description | Source |
|---|---|---|
| `VERCEL_TOKEN` | Vercel Personal Access Token | [Vercel Account Tokens](https://vercel.com/account/tokens) |
| `VERCEL_ORG_ID` | Vercel Organization / User ID | Found in `frontend/.vercel/project.json` or team settings |
| `VERCEL_PROJECT_ID` | Vercel Project ID | Found in Project Settings on Vercel |
| `MONGODB_URI` | MongoDB Atlas Connection String | MongoDB Atlas Cluster Dashboard |
| `GEMINI_API_KEY` | Google Gemini API Key | [Google AI Studio](https://aistudio.google.com) |

---

## 4. Ingestion Webhook Integration

Configure your CI/CD, Kubernetes Alertmanager, or Docker daemon to post polymorphic error payloads to NetPulse:

```bash
curl -X POST http://localhost:8000/api/webhook/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "github-actions",
    "service_name": "checkout-api",
    "environment": "production",
    "level": "CRITICAL",
    "error_message": "PostgreSQL connection pool exhausted: timeout waiting for connection",
    "stack_trace": "asyncpg.exceptions.TooManyConnectionsError: timeout waiting for connection\nFile checkout.py line 184",
    "git_metadata": {
      "commit_hash": "a4f89d2",
      "author": "sre@company.com",
      "branch": "main",
      "commit_message": "feat(checkout): parallel queries without connection pool limit"
    }
  }'
```
NetPulse immediately generates the embedding, finds top similar past incidents, links the verified runbook, and broadcasts the event live to the command center.
