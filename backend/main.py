from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from api import auth, admin

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

app.include_router(auth.router)
app.include_router(admin.router)

@app.on_event("startup")
async def startup():
    from core.database import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
def root():
    return {"message": "D&D Play-by-Post API v2.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
