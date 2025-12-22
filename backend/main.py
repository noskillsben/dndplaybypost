from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from api import schemas, compendium

app = FastAPI(title="D&D Platform API v2.0")

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(schemas.router)
app.include_router(compendium.router)

@app.get("/")
async def root():
    return {"message": "D&D Platform API v2.0 is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
