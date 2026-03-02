from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import orders, master_data, export
from app.services import rag_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Initialising Qdrant collections...")
    try:
        rag_service.init_collections()
    except Exception as exc:
        logger.warning("Qdrant init failed (will retry on first use): %s", exc)
    yield
    # Shutdown (nothing to clean up)


app = FastAPI(
    title="PO Processing Pipeline API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders.router)
app.include_router(master_data.router)
app.include_router(export.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
