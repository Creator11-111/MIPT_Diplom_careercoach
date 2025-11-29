"""
Загрузка финансовых вакансий из Parquet файла в MongoDB.
"""

from __future__ import annotations

import os
from typing import Any

import polars as pl

from app.db.mongo import get_db


PARQUET_PATH = os.environ.get(
    "VACANCIES_PARQUET_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "financial_vacancies.parquet"),
)


async def seed_vacancies_if_needed() -> None:
    """Загружает финансовые вакансии из Parquet файла в MongoDB."""
    if not os.path.exists(PARQUET_PATH):
        print(f"⚠️  Файл с вакансиями не найден: {PARQUET_PATH}")
        print("📝 Создайте файл через конвертацию CSV или парсинг HH.ru")
        return

    print(f"📂 Загрузка вакансий из: {PARQUET_PATH}")

    df = pl.read_parquet(PARQUET_PATH)
    print(f"✅ Загружено {len(df)} вакансий из файла")

    required_cols: dict[str, Any] = {
        "idx": pl.UInt32,
        "№": pl.Int64,
        "id": pl.Int64,
        "title": pl.Utf8,
        "salary": pl.Utf8,
        "experience": pl.Utf8,
        "job_type": pl.Utf8,
        "description": pl.Utf8,
        "key_skills": pl.Utf8,
        "company": pl.Utf8,
        "location": pl.Utf8,
        "date_of_post": pl.Utf8,
        "type": pl.Utf8,
    }

    for col, dtype in required_cols.items():
        if col not in df.columns:
            df = df.with_columns(pl.lit(None).cast(dtype).alias(col))
        else:
            df = df.with_columns(pl.col(col).cast(dtype, strict=False))

    df = df.select(list(required_cols.keys()))

    db = await get_db()
    coll = db["vacancies"]

    print("🔍 Проверяю существующие вакансии в базе...")
    existing = set()
    async for doc in coll.find({}, {"idx": 1}):
        if "idx" in doc:
            existing.add(int(doc["idx"]))

    print(f"📊 Найдено {len(existing)} существующих вакансий")

    to_insert = [
        {k: (None if v == "" else v) for k, v in row.items()}
        for row in df.to_dicts()
        if int(row.get("idx", -1)) not in existing
    ]

    if to_insert:
        print(f"💾 Добавляю {len(to_insert)} новых вакансий в базу...")
        await coll.create_index("idx")
        await coll.insert_many(to_insert)
        print("✅ Вакансии добавлены")
    else:
        print("ℹ️  Все вакансии уже загружены")

    total_count = await coll.count_documents({})
    print(f"📊 Всего вакансий в базе: {total_count}")








