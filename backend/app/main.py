import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routes import webhook, incidents, chaos, runbooks, topology, health
from app.services.websocket_manager import ws_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("netpulse.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}...")
    await connect_to_mongo()
    yield
    # Shutdown
    logger.info("Shutting down NetPulse...")
    await close_mongo_connection()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous, self-healing infrastructure & CI/CD incident-triage and root-cause analysis platform",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes
app.include_router(webhook.router, prefix=settings.API_PREFIX)
app.include_router(incidents.router, prefix=settings.API_PREFIX)
app.include_router(chaos.router, prefix=settings.API_PREFIX)
app.include_router(runbooks.router, prefix=settings.API_PREFIX)
app.include_router(topology.router, prefix=settings.API_PREFIX)
app.include_router(health.router, prefix=settings.API_PREFIX)

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    """Real-time live WebSocket stream for incidents, telemetry spikes, and remediation logs."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keepalive ping/pong and client message listener
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"event": "pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket client error: {e}")
        ws_manager.disconnect(websocket)

@app.get("/api/stream/events")
async def sse_events_endpoint():
    """Server-Sent Events (SSE) alternative for firewalled/HTTP-only environments."""
    async def event_generator():
        queue = asyncio.Queue()
        
        # We can yield heartbeats
        while True:
            await asyncio.sleep(15)
            yield f"event: heartbeat\ndata: {{\"timestamp\": \"{asyncio.get_event_loop().time()}\"}}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
