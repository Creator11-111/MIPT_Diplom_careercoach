"""
Скрипт для конвертации CSV базы HeadHunter в Parquet формат

Этот скрипт:
1. Читает CSV файл Raw_Jobs.csv с вакансиями
2. Фильтрует финансовые вакансии по ключевым словам
3. Конвертирует в формат Parquet с нужными полями
4. Сохраняет в financial_coach/data/financial_vacancies.parquet

Использование:
    python financial_coach/data_parsing/convert_csv_to_parquet.py
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import re

import pandas as pd
import polars as pl
from tqdm import tqdm

# Финансовые ключевые слова для фильтрации
FINANCIAL_KEYWORDS = [
    "финанс",
    "банк",
    "бухгалтер",
    "аудитор",
    "казначей",
    "кредит",
    "инвестиц",
    "риск-менедж",
    "банковск",
    "финансовый аналитик",
    "финансовый директор",
    "финансовый менеджер",
    "cfo",
    "банковский специалист",
    "кредитный специалист",
    "инвестиционный менеджер",
    "аналитик по кредитным рискам",
    "специалист по мсфо",
    "финансовый контролер",
    "специалист по финансовому планированию",
    "treasurer",
    "accountant",
    "auditor",
    "financial analyst",
    "financial manager",
    "bank",
    "credit",
    "investment",
    "риск-менеджмент",
    "управленческий учет",
    "финансовый учет",
    "бюджетирование",
    "финансовое планирование",
    "финансовая отчетность",
]


def normalize_column_name(col_name: str) -> str:
    """Нормализует название колонки."""
    normalized = col_name.strip().lower().replace(" ", "_")
    normalized = re.sub(r"[^\w_]", "", normalized)
    return normalized


def build_column_mapping(df_columns: List[str]) -> Dict[str, str]:
    """Ищет соответствие между колонками CSV и требуемыми полями."""
    normalized_cols = {normalize_column_name(col): col for col in df_columns}

    required = {
        "idx": ["idx", "id", "номер", "number", "№"],
        "title": ["title", "название", "name", "должность", "position", "job_title"],
        "description": ["description", "описание", "описание_вакансии", "текст", "text"],
        "company": ["company", "компания", "employer", "работодатель"],
        "location": ["location", "локация", "город", "city", "area", "регион"],
        "salary": ["salary", "зарплата", "оклад", "payment"],
        "experience": ["experience", "опыт", "опыт_работы", "experience_required"],
        "key_skills": ["key_skills", "навыки", "skills", "требования", "requirements", "компетенции"],
        "job_type": ["job_type", "тип_работы", "employment", "занятость", "формат"],
        "date_of_post": ["date_of_post", "дата", "date", "published_at", "дата_публикации"],
    }

    mapping: Dict[str, str] = {}
    for target, candidates in required.items():
        for candidate in candidates:
            key = normalize_column_name(candidate)
            if key in normalized_cols:
                mapping[target] = normalized_cols[key]
                break
    return mapping


def is_financial_vacancy(row: Dict[str, Any], title_col: str, desc_col: Optional[str]) -> bool:
    """Возвращает True, если вакансия относится к финансовому сектору."""
    text_parts = [str(row.get(title_col, "") or "").lower()]
    if desc_col:
        text_parts.append(str(row.get(desc_col, "") or "").lower())
    text = " ".join(text_parts)

    return any(keyword in text for keyword in FINANCIAL_KEYWORDS)


def convert_csv_to_parquet(csv_path: str, output_path: str, sample_size: Optional[int] = None) -> None:
    """Конвертирует CSV в Parquet, отфильтровав финансовые вакансии."""
    print("=" * 60)
    print("🔄 КОНВЕРТАЦИЯ CSV В PARQUET")
    print("=" * 60)
    print()

    if not os.path.exists(csv_path):
        print(f"❌ Файл не найден: {csv_path}")
        return

    print(f"📂 Читаю CSV: {csv_path}")

    chunk_size = 10_000
    total_rows = 0
    financial_rows = 0
    vacancies: List[Dict[str, Any]] = []

    try:
        preview = pd.read_csv(
            csv_path,
            nrows=1_000,
            encoding="utf-8",
            low_memory=False,
            on_bad_lines="skip",
            sep=";",
        )
        print(f"✅ Найдены колонки: {list(preview.columns)}")

        column_mapping = build_column_mapping(list(preview.columns))
        print("📋 Соответствие колонок:")
        for target, source in column_mapping.items():
            print(f"   {target} ← {source}")
        print()

        title_col = column_mapping.get("title") or preview.columns[0]
        desc_col = column_mapping.get("description")

        iterator = pd.read_csv(
            csv_path,
            chunksize=chunk_size,
            encoding="utf-8",
            low_memory=False,
            on_bad_lines="skip",
            nrows=sample_size,
            sep=";",
        )

        for chunk_index, chunk in enumerate(iterator, start=1):
            print(f"📦 Обрабатываю блок {chunk_index} ({len(chunk)} строк)")
            for _, row in tqdm(chunk.iterrows(), total=len(chunk), desc=f"Блок {chunk_index}"):
                total_rows += 1
                row_dict = row.to_dict()

                if is_financial_vacancy(row_dict, title_col, desc_col):
                    financial_rows += 1
                    idx_value = row_dict.get(column_mapping.get("idx", "id"), total_rows)
                    vacancy = {
                        "idx": int(idx_value),
                        "№": int(idx_value),
                        "id": int(idx_value),
                        "title": str(row_dict.get(title_col, "") or ""),
                        "salary": str(row_dict.get(column_mapping.get("salary", ""), "") or ""),
                        "experience": str(row_dict.get(column_mapping.get("experience", ""), "") or ""),
                        "job_type": str(row_dict.get(column_mapping.get("job_type", ""), "") or ""),
                        "description": str(row_dict.get(desc_col, "") or "") if desc_col else "",
                        "key_skills": str(row_dict.get(column_mapping.get("key_skills", ""), "") or ""),
                        "company": str(row_dict.get(column_mapping.get("company", ""), "") or ""),
                        "location": str(row_dict.get(column_mapping.get("location", ""), "") or ""),
                        "date_of_post": str(row_dict.get(column_mapping.get("date_of_post", ""), "") or ""),
                        "type": "financial",
                    }
                    vacancies.append(vacancy)

            print(f"   ✅ Финансовых вакансий найдено: {financial_rows} из {total_rows}")

        print("=" * 60)
        print(f"📊 Всего строк: {total_rows}")
        print(f"📊 Финансовых вакансий: {financial_rows}")
        print("=" * 60)

        if not vacancies:
            print("❌ Финансовых вакансий не найдено. Проверьте ключевые слова или структуру CSV.")
            return

        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)

        df_final = pl.DataFrame(vacancies)
        df_final.write_parquet(output_path, compression="snappy")

        size_mb = os.path.getsize(output_path) / 1024 / 1024
        print(f"✅ Parquet сохранён: {output_path} ({size_mb:.2f} MB)")
        print()
        print("📝 Следующий шаг: python financial_coach/data_parsing/generate_embeddings.py")

    except Exception as exc:  # noqa: BLE001
        print(f"❌ Ошибка при обработке: {exc}")
        raise


def main() -> None:
    """Точка входа."""
    project_root = Path(__file__).parent.parent.parent
    candidates = [
        project_root / "Raw_Jobs.csv",
        Path("Raw_Jobs.csv"),
    ]

    csv_path = next((path for path in candidates if path.exists()), None)
    if csv_path is None:
        print("❌ Файл Raw_Jobs.csv не найден. Поместите его в корень проекта.")
        return

    output_path = Path(__file__).parent.parent / "data" / "financial_vacancies.parquet"
    convert_csv_to_parquet(str(csv_path), str(output_path))


if __name__ == "__main__":
    main()


