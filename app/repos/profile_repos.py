"""
Репозиторий для работы с профилями пользователей

Профили содержат структурированную информацию о финансовом специалисте:
- Опыт работы
- Навыки
- Цели
- Предпочтения
"""

from __future__ import annotations

from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import sanitize_mongo_doc


class ProfilesRepository:
    """Репозиторий для работы с профилями пользователей"""
    
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._coll = db["profiles"]

    async def find_by_user_id(self, user_id: str) -> Optional[dict[str, Any]]:
        """Найти профиль по user_id"""
        doc = await self._coll.find_one({"user_id": user_id})
        return sanitize_mongo_doc(doc)
    
    async def find_by_session_id(self, session_id: str) -> Optional[dict[str, Any]]:
        """Найти профиль по session_id"""
        doc = await self._coll.find_one({"session_id": session_id})
        return sanitize_mongo_doc(doc)
    
    async def insert_one(self, profile: dict[str, Any]) -> None:
        """Создать новый профиль"""
        await self._coll.insert_one(profile)
    
    async def update_one(self, user_id: str, update: dict[str, Any]) -> None:
        """Обновить профиль"""
        await self._coll.update_one({"user_id": user_id}, {"$set": update})
    
    async def upsert_one(self, profile: dict[str, Any]) -> None:
        """Создать или обновить профиль"""
        await self._coll.update_one(
            {"user_id": profile["user_id"]},
            {"$set": profile},
            upsert=True
        )





