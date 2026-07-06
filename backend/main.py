# basic imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings

# api imports, core of the application
from api import schemas, compendium, systems
from api.routes import actors

settings = get_settings()

app = FastAPI(title="D&D Platform API v2.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(schemas.router)
app.include_router(compendium.router)
app.include_router(systems.router)
app.include_router(actors.router)

@app.get("/")
async def root():
    return {"message": "D&D Platform API v2.0 is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
