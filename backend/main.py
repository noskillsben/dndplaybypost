from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from api import auth, admin, campaigns, characters, dice
from api.messages import campaign_messages_router, messages_router

app = FastAPI(title="D&D Play-by-Post API", version="2.0")

# CORS Configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(campaigns.router, prefix="/api")
app.include_router(characters.router, prefix="/api")
app.include_router(campaign_messages_router, prefix="/api")
app.include_router(messages_router, prefix="/api")
app.include_router(dice.router, prefix="/api")

@app.on_event("startup")
async def startup():
    from core.database import engine, Base
    # Import all models to ensure they're registered
    from models import user, campaign, campaign_member, character, message
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
def root():
    return {"message": "D&D Play-by-Post API v2.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
