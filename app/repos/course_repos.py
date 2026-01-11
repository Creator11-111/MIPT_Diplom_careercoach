"""
Репозиторий для работы с курсами

Курсы уже загружены в MongoDB через seed_courses.py (если есть)
Этот репозиторий позволяет их искать и получать.
"""

from __future__ import annotations

from typing import Any, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import sanitize_mongo_doc, sanitize_many


class CoursesRepository:
    """Репозиторий для работы с курсами"""
    
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._coll = db["courses"]

    async def find_by_idx(self, idx: int) -> Optional[dict[str, Any]]:
        """Найти курс по idx"""
        doc = await self._coll.find_one({"idx": idx})
        return sanitize_mongo_doc(doc)
    
    async def find_by_ids(self, idx_list: List[int]) -> List[dict[str, Any]]:
        """Найти курсы по списку idx"""
        cursor = self._coll.find({"idx": {"$in": idx_list}})
        docs = [d async for d in cursor]
        return sanitize_many(docs)
    
    async def count_total(self) -> int:
        """Получить общее количество курсов"""
        return await self._coll.count_documents({})





