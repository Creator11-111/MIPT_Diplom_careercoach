"""
Financial Career Coach Application Entry Point

FastAPI application implementing AI-powered career guidance system
for financial sector professionals.
"""

from contextlib import asynccontextmanager
import logging
import sys
import os
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import Settings, get_settings
from app.middleware.rate_limit import RateLimitMiddleware
from app.db.mongo import init_mongo, close_mongo, ensure_indexes
from app.startup.seed_vacancies import seed_vacancies_if_needed
from app.startup.load_embeddings import build_faiss, get_index_stats
from app.models.schemas import HealthResponse

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager
    
    Initialization is performed synchronously to ensure FAISS index
    is ready before accepting requests.
    """
    settings: Settings = get_settings()
    
    # Валидация настроек при старте
    try:
        settings.validate_required()
        logger.info("✅ Configuration validated")
    except ValueError as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        if settings.app_env == "production":
            raise  # Fail fast in production
        else:
            logger.warning("⚠️ Continuing with invalid config (development mode)")
    
    logger.info("🚀 Starting Financial Career Coach...")
    
    # 1. Инициализация MongoDB (опционально в dev-режиме)
    logger.info("📦 Connecting to MongoDB...")
    mongo_available = False
    try:
        await init_mongo(settings)
        await ensure_indexes()
        logger.info("✅ MongoDB connected")
        mongo_available = True
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        if settings.app_env == "production":
            raise
        else:
            logger.warning("⚠️ Continuing without MongoDB (development mode) - API calls will fail but frontend will work")
    
    # 2. Загрузка данных (только если MongoDB доступна)
    if mongo_available:
        logger.info("📊 Loading vacancies data...")
        try:
            await seed_vacancies_if_needed()
            logger.info("✅ Vacancies data loaded")
        except Exception as e:
            logger.warning(f"⚠️ Failed to seed vacancies: {e}")
    else:
        logger.info("⏭️ Skipping vacancies seeding (no MongoDB)")
    
    # 3. Build FAISS index (required for semantic search)
    logger.info("🔍 Building FAISS index...")
    try:
        build_faiss()
        stats = get_index_stats()
        if stats["index_built"]:
            logger.info(f"✅ FAISS index built: {stats['vacancies_count']} vacancies")
        else:
            logger.error("❌ FAISS index NOT built!")
            logger.error(f"   Embeddings dir: {stats['embeddings_dir']}")
            logger.error(f"   FAISS available: {stats['faiss_available']}")
    except Exception as e:
        logger.error(f"❌ FAISS build failed: {e}", exc_info=True)
    
    logger.info("✅ Application ready!")
    
    # Сохраняем состояние MongoDB в app.state
    app.state.mongo_available = mongo_available
    
    try:
        yield
    finally:
        logger.info("🛑 Shutting down...")
        if mongo_available:
            await close_mongo()
        logger.info("✅ Shutdown complete")


# Создание FastAPI приложения
app = FastAPI(
    title="Financial Career Coach API",
    description="AI-система карьерного коучинга для финансового сектора",
    version="1.0.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# Middleware - CORS настройки из конфигурации
settings = get_settings()
cors_origins = settings.get_cors_origins_list()

if "*" in cors_origins:
    logger.warning("⚠️ CORS allows all origins - not recommended for production!")

app.add_middleware(
    CORSMiddleware, 
    allow_origins=cors_origins,
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Rate limiting middleware (configurable via settings)
settings_for_middleware = get_settings()
app.add_middleware(
    RateLimitMiddleware,
    requests_per_window=settings_for_middleware.rate_limit_requests,
    window_seconds=settings_for_middleware.rate_limit_window
)


@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint для Cloud Run"""
    return HealthResponse(status="ok", time=datetime.utcnow().isoformat())


@app.get("/ready")
async def ready():
    """Проверка готовности системы (для фронтенда)"""
    from app.startup.load_embeddings import faiss_index, vacancy_ids
    is_ready = faiss_index is not None and len(vacancy_ids) > 0
    return {
        "ready": is_ready,
        "faiss_built": faiss_index is not None,
        "vacancies_count": len(vacancy_ids),
        "time": datetime.utcnow().isoformat()
    }


@app.get("/debug")
async def debug():
    """Отладочная информация о состоянии системы"""
    from app.startup.load_embeddings import faiss_index, vacancy_ids
    stats = get_index_stats()
    return {
        "ready": faiss_index is not None and len(vacancy_ids) > 0,
        "port": os.getenv("PORT", "8080"),
        "faiss": {
            "index_built": faiss_index is not None,
            "vacancies_count": len(vacancy_ids),
            "embeddings_dir": stats.get("embeddings_dir", ""),
            "faiss_available": stats.get("faiss_available", False),
        }
    }


@app.get("/")
async def root():
    """Корневой endpoint - возвращает веб-интерфейс"""
    static_file = os.path.join(os.path.dirname(__file__), "..", "static", "index.html")
    if os.path.exists(static_file):
        return FileResponse(static_file)
    return {
        "message": "Financial Career Coach API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# Подключение роутеров
from app.routers.sessions import router as sessions_router
from app.routers.chat import router as chat_router
from app.routers.profile import router as profile_router
from app.routers.match import router as match_router
from fastapi import APIRouter

# Создаем версионированный роутер
api_v1 = APIRouter(prefix="/v1")

# Подключаем роутеры к версионированному API
api_v1.include_router(sessions_router, prefix="/sessions", tags=["sessions"])
api_v1.include_router(chat_router, prefix="/chat", tags=["chat"])
api_v1.include_router(profile_router, prefix="/profile", tags=["profile"])
api_v1.include_router(match_router, prefix="/match", tags=["match"])

# Подключаем версионированный API к приложению
app.include_router(api_v1)

# Backward compatibility: также подключаем без версии (перенаправление на v1)
# Это позволяет старым клиентам продолжать работать
app.include_router(sessions_router, prefix="/sessions", tags=["sessions-deprecated"])
app.include_router(chat_router, prefix="/chat", tags=["chat-deprecated"])
app.include_router(profile_router, prefix="/profile", tags=["profile-deprecated"])
app.include_router(match_router, prefix="/match", tags=["match-deprecated"])

# Подключение статических файлов (веб-интерфейс)
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=True
    )
