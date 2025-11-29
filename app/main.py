"""
Главный файл приложения финансового карьерного коуча

Это точка входа FastAPI приложения. Здесь настраивается сервер,
подключаются роутеры и инициализируются данные.
"""

from contextlib import asynccontextmanager
import logging
import sys
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import Settings, get_settings
from app.db.mongo import init_mongo, close_mongo, ensure_indexes
from app.startup.seed_vacancies import seed_vacancies_if_needed
from app.startup.load_embeddings import build_faiss
from app.models.schemas import HealthResponse

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения
    
    При запуске:
    - Инициализирует MongoDB
    - Создает индексы
    - Загружает вакансии и курсы (если нужно)
    - Строит FAISS индексы для поиска
    
    При остановке:
    - Закрывает подключения к базе данных
    """
    settings: Settings = get_settings()
    
    logger.info("🚀 Запуск финансового карьерного коуча...")
    
    # Инициализация MongoDB
    logger.info("📦 Подключение к MongoDB...")
    await init_mongo(settings)
    await ensure_indexes()
    logger.info("✅ MongoDB подключена")
    
    # Загрузка данных
    await seed_vacancies_if_needed()
    
    # Построение FAISS индексов для поиска
    logger.info("🔍 Построение индексов для поиска...")
    build_faiss()
    
    logger.info("✅ Приложение готово к работе!")
    
    try:
        yield
    finally:
        # Закрытие подключений при остановке
        logger.info("🛑 Закрытие подключений...")
        await close_mongo()
        logger.info("✅ Подключения закрыты")


# Создание FastAPI приложения
app = FastAPI(
    title="Financial Career Coach API",
    description="AI-система карьерного коучинга для финансового сектора",
    version="1.0.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    Проверка работоспособности API
    
    Returns:
        HealthResponse с статусом "ok" и текущим временем
    """
    return HealthResponse(status="ok", time=datetime.utcnow().isoformat())


@app.get("/")
async def root():
    """Корневой endpoint - перенаправляет на веб-интерфейс"""
    from fastapi.responses import FileResponse
    import os
    static_file = os.path.join(os.path.dirname(__file__), "..", "static", "index.html")
    if os.path.exists(static_file):
        return FileResponse(static_file)
    return {
        "message": "Financial Career Coach API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "web_interface": "/static/index.html",
    }


# Подключение роутеров
from app.routers import sessions, chat, profile, match

app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(profile.router, prefix="/profile", tags=["profile"])
app.include_router(match.router, prefix="/match", tags=["match"])

# Подключение статических файлов (веб-интерфейс)
import os
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")



if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
    )






