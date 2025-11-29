"""
Репозитории для работы с сессиями и сообщениями

Репозитории - это слой доступа к данным. Они отвечают за:
- Сохранение и загрузку сессий из MongoDB
- Сохранение и загрузку сообщений из MongoDB
"""

from __future__ import annotations

from typing import Any, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import sanitize_mongo_doc, sanitize_many


class SessionsRepository:
    """Репозиторий для работы с сессиями чата"""
    
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._coll = db["sessions"]

    async def find_by_id(self, session_id: str) -> Optional[dict[str, Any]]:
        """Найти сессию по ID"""
        doc = await self._coll.find_one({"session_id": session_id})
        return sanitize_mongo_doc(doc)
    
    async def insert_one(self, session: dict[str, Any]) -> None:
        """Создать новую сессию"""
        await self._coll.insert_one(session)
    
    async def update_one(self, session_id: str, update: dict[str, Any]) -> None:
        """Обновить сессию"""
        await self._coll.update_one({"session_id": session_id}, {"$set": update})
    
    async def list_by_user_id(self, user_id: str, limit: int = 100) -> List[dict[str, Any]]:
        """Получить все сессии пользователя, отсортированные по дате создания (новые первые)"""
        cursor = self._coll.find({"user_id": user_id}).sort("state.last_updated_at", -1).limit(int(limit))
        docs = [d async for d in cursor]
        return sanitize_many(docs)
    
    async def delete_by_id(self, session_id: str) -> None:
        """Удалить сессию по ID"""
        await self._coll.delete_one({"session_id": session_id})


class MessagesRepository:
    """Репозиторий для работы с сообщениями"""
    
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._coll = db["messages"]

    async def list_by_session(self, session_id: str, limit: int = 40) -> List[dict[str, Any]]:
        """Получить последние сообщения сессии"""
        cursor = self._coll.find({"session_id": session_id}).sort("created_at", 1).limit(int(limit))
        docs = [d async for d in cursor]
        return sanitize_many(docs)

    async def insert_one(self, message: dict[str, Any]) -> None:
        """Сохранить сообщение"""
        await self._coll.insert_one(message)

    async def find_last_assistant_message(self, session_id: str) -> Optional[dict[str, Any]]:
        """Найти последнее сообщение ассистента"""
        doc = await self._coll.find_one(
            {"session_id": session_id, "role": "assistant"}, 
            sort=[("created_at", -1)]
        )
        return sanitize_mongo_doc(doc)
    
    async def get_all_by_session(self, session_id: str) -> List[dict[str, Any]]:
        """Получить все сообщения сессии (без лимита)"""
        cursor = self._coll.find({"session_id": session_id}).sort("created_at", 1)
        docs = [d async for d in cursor]
        return sanitize_many(docs)
    
    async def delete_by_session_id(self, session_id: str) -> None:
        """Удалить все сообщения сессии"""
        await self._coll.delete_many({"session_id": session_id})

