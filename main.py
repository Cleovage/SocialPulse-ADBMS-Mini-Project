from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import uvicorn
import os

from app.config import settings
from app.database import Database
from app.seed_data import seed_database
from app.routers import overview, influencers, trends, campaigns, geo, adbms_lab, instagram

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("socialpulse.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB, ensure indexes, check seed data
    logger.info("Initializing SocialPulse Analytics Platform...")
    Database.connect_db()
    
    # Auto-seed if database is empty
    seed_result = seed_database(force=False)
    logger.info(f"Database readiness status: {seed_result}")
    
    yield
    
    # Shutdown: Close database connection
    logger.info("Shutting down SocialPulse Analytics Platform...")
    Database.close_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Advanced Database Management System (ADBMS) Mini Project - Social Media Trend & Influencer Analytics Platform using MongoDB",
    version=settings.VERSION,
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(overview.router)
app.include_router(influencers.router)
app.include_router(trends.router)
app.include_router(campaigns.router)
app.include_router(geo.router)
app.include_router(adbms_lab.router)
app.include_router(instagram.router)

# Mount Static Files (Frontend UI)
static_dir = os.path.join(os.path.dirname(__file__), "app", "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
