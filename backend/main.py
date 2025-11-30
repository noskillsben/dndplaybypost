from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from api import auth, admin, campaigns, characters, dice, users, websocket
from api.messages import campaign_messages_router, messages_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from core.database import engine, Base
    # Import all models to ensure they're registered
    from models import user, campaign, campaign_member, character, message
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown (if needed in the future)

app = FastAPI(title="D&D Play-by-Post API", version="2.0", lifespan=lifespan)

# CORS Configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    import logging
    logger = logging.getLogger("uvicorn")
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    return response

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(campaigns.router, prefix="/api")
app.include_router(characters.router, prefix="/api")
app.include_router(campaign_messages_router, prefix="/api")
app.include_router(messages_router, prefix="/api")
app.include_router(dice.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(websocket.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "D&D Play-by-Post API v2.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
