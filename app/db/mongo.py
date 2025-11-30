"""
Работа с базой данных MongoDB

Этот модуль содержит функции для:
- Подключения к MongoDB
- Создания индексов для быстрого поиска
- Очистки документов от служебных полей
"""

from __future__ import annotations

from typing import Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import Settings

# Глобальные переменные для хранения подключения
_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def init_mongo(settings: Settings) -> None:
    """
    Инициализация подключения к MongoDB
    
    Args:
        settings: Настройки приложения с параметрами подключения
    """
    global _client, _db
    if _client is not None:
        return
    _client = AsyncIOMotorClient(settings.mongo_uri)
    _db = _client[settings.mongo_db]


async def get_db() -> AsyncIOMotorDatabase:
    """
    Получение экземпляра базы данных
    
    Returns:
        AsyncIOMotorDatabase объект
        
    Raises:
        RuntimeError: Если MongoDB не инициализирована
    """
    if _db is None:
        raise RuntimeError("MongoDB is not initialized")
    return _db


async def close_mongo() -> None:
    """Закрытие подключения к MongoDB"""
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None


async def ensure_indexes() -> None:
    """
    Создание индексов для оптимизации запросов
    
    Индексы ускоряют поиск по базе данных.
    """
    db = await get_db()
    await db["sessions"].create_index("user_id")
    await db["profiles"].create_index("user_id")
    await db["messages"].create_index([("session_id", 1), ("created_at", 1)])
    await db["vacancies"].create_index("idx")
    await db["courses"].create_index("idx")


def sanitize_mongo_doc(doc: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """
    Удаление служебного поля _id из документа MongoDB
    
    Args:
        doc: Документ из MongoDB
        
    Returns:
        Документ без поля _id
    """
    if doc is None:
        return None
    if "_id" in doc:
        doc = {k: v for k, v in doc.items() if k != "_id"}
    return doc


def sanitize_many(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Удаление _id из списка документов
    
    Args:
        docs: Список документов из MongoDB
        
    Returns:
        Список документов без поля _id
    """
    return [sanitize_mongo_doc(d) or {} for d in docs]














