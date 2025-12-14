from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from api import auth, admin, campaigns, characters, dice, users, websocket, compendium, compendium_admin
from api.messages import campaign_messages_router, messages_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from core.database import engine, Base, AsyncSessionLocal
    # Import all models to ensure they're registered
    from models import user, campaign, campaign_member, character, message, compendium, site_settings
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Auto-import SRD content if enabled and compendium is empty
    auto_import = os.getenv("AUTO_IMPORT_SRD", "true").lower() == "true"
    if auto_import:
        from services.import_service import check_compendium_empty, ImportService
        import logging
        logger = logging.getLogger("uvicorn")
        
        async with AsyncSessionLocal() as db:
            is_empty = await check_compendium_empty(db)
            if is_empty:
                logger.info("Compendium is empty. Auto-importing SRD content...")
                try:
                    import_service = ImportService(db)
                    
                    # Import component templates first
                    srd_path = os.getenv("SRD_DATA_PATH", "backend/data/srd/")
                    template_file = os.path.join(srd_path, "component_templates.json")
                    if os.path.exists(template_file):
                        await import_service.import_component_templates(template_file)
                        logger.info("Component templates imported")
                    
                    # Import SRD content
                    stats = await import_service.import_srd_content()
                    logger.info(f"SRD import complete: {stats}")
                except Exception as e:
                    logger.error(f"Failed to auto-import SRD content: {e}")
            else:
                logger.info("Compendium already has content. Skipping auto-import.")
    
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
app.include_router(compendium.router, prefix="/api")
app.include_router(compendium_admin.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "D&D Play-by-Post API v2.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
