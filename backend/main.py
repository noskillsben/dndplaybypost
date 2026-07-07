# basic imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from core.errors import register_exception_handlers

# api imports, core of the application
from api import schemas, compendium, compendiums, systems, templates

settings = get_settings()

app = FastAPI(title="D&D Platform API v2.0")

register_exception_handlers(app)

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
app.include_router(compendiums.router)
app.include_router(systems.router)
app.include_router(templates.router)

@app.get("/")
async def root():
    return {"message": "D&D Platform API v2.0 is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
