import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import CollectionInvalid, OperationFailure
from app.config import settings

logger = logging.getLogger("netpulse.database")

class Database:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None
    is_atlas_vector_search_ready: bool = False

db_manager = Database()

async def connect_to_mongo():
    logger.info(f"Connecting to MongoDB at: {settings.MONGODB_URI.split('@')[-1]}")
    db_manager.client = AsyncIOMotorClient(
        settings.MONGODB_URI,
        serverSelectionTimeoutMS=5000,
    )
    db_manager.db = db_manager.client[settings.MONGODB_DATABASE]
    
    # Verify connection
    try:
        await db_manager.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB!")
    except Exception as e:
        logger.warning(f"Could not connect to MongoDB server: {e}. Will operate with graceful fallback mode.")
    
    await init_collections()

async def close_mongo_connection():
    if db_manager.client:
        db_manager.client.close()
        logger.info("Closed MongoDB connection.")

async def init_collections():
    """Initializes time series collections, regular collections, and indexes."""
    if db_manager.db is None:
        return
        
    try:
        existing_collections = await db_manager.db.list_collection_names()
        
        # 1. Create raw_events as Time Series Collection
        if "raw_events" not in existing_collections:
            try:
                await db_manager.db.create_collection(
                    "raw_events",
                    timeseries={
                        "timeField": "timestamp",
                        "metaField": "service_name",
                        "granularity": "seconds",
                    },
                    expireAfterSeconds=60 * 60 * 24 * 7 # 7 days retention
                )
                logger.info("Created 'raw_events' as a MongoDB Time Series Collection.")
            except OperationFailure as e:
                logger.warning(f"Time series collection creation not supported by current MongoDB server ({e}). Creating standard collection.")
                await db_manager.db.create_collection("raw_events")
        
        # 2. Indexes for raw_events
        raw_events = db_manager.db["raw_events"]
        await raw_events.create_index([("service_name", 1), ("timestamp", -1)])
        await raw_events.create_index([("metric_type", 1), ("timestamp", -1)])
        
        # 3. Create incidents collection & indexes
        incidents = db_manager.db["incidents"]
        await incidents.create_index([("incident_id", 1)], unique=True)
        await incidents.create_index([("service_name", 1), ("created_at", -1)])
        await incidents.create_index([("status", 1)])
        await incidents.create_index([("severity", 1)])
        await incidents.create_index([("created_at", -1)])
        
        # 4. Create runbooks collection & indexes
        runbooks = db_manager.db["runbooks"]
        await runbooks.create_index([("runbook_id", 1)], unique=True)
        await runbooks.create_index([("service_name", 1)])
        await runbooks.create_index([("error_signature", 1)])

        # 5. Check if Atlas Vector Search is available
        await check_vector_search_support()
        
    except Exception as e:
        logger.error(f"Error during collections/indexes initialization: {e}")

async def check_vector_search_support():
    """Probes if MongoDB Atlas $vectorSearch stage is supported."""
    try:
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": [0.0] * settings.EMBEDDING_DIMENSIONS,
                    "numCandidates": 1,
                    "limit": 1
                }
            }
        ]
        cursor = db_manager.db["incidents"].aggregate(pipeline)
        await cursor.to_list(length=1)
        db_manager.is_atlas_vector_search_ready = True
        logger.info("MongoDB Atlas $vectorSearch is available and active!")
    except Exception as e:
        db_manager.is_atlas_vector_search_ready = False
        logger.info(f"Atlas Vector Search not active ({type(e).__name__}). Using high-performance Python vector cosine fallback.")

def get_database() -> AsyncIOMotorDatabase:
    return db_manager.db
