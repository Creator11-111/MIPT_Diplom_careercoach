"""
Репозиторий для работы с вакансиями

Вакансии уже загружены в MongoDB через seed_vacancies.py
Этот репозиторий позволяет их искать и получать.
"""

from __future__ import annotations

from typing import Any, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import sanitize_mongo_doc, sanitize_many


class VacanciesRepository:
    """Репозиторий для работы с вакансиями"""
    
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._coll = db["vacancies"]

    async def find_by_idx(self, idx: int) -> Optional[dict[str, Any]]:
        """Найти вакансию по idx"""
        doc = await self._coll.find_one({"idx": idx})
        return sanitize_mongo_doc(doc)
    
    async def find_by_ids(self, idx_list: List[int]) -> List[dict[str, Any]]:
        """Найти вакансии по списку idx"""
        cursor = self._coll.find({"idx": {"$in": idx_list}})
        docs = [d async for d in cursor]
        return sanitize_many(docs)
    
    async def count_total(self) -> int:
        """Получить общее количество вакансий"""
        return await self._coll.count_documents({})
    
    async def find_all(self, limit: int = 100) -> List[dict[str, Any]]:
        """Найти все вакансии (для отладки)"""
        cursor = self._coll.find({}).limit(limit)
        docs = [d async for d in cursor]
        return sanitize_many(docs)





