"""
Скрипт для генерации эмбеддингов финансовых вакансий

Эмбеддинги - это векторы чисел, которые представляют смысл текста.
Похожие тексты имеют похожие эмбеддинги.

Этот скрипт:
1. Загружает вакансии из Parquet файла
2. Для каждой вакансии создает эмбеддинг через YandexGPT
3. Сохраняет эмбеддинги в файлы для быстрого поиска
4. Строит FAISS индексы для семантического поиска

ВАЖНО: Требуется API ключ YandexGPT!
"""

from __future__ import annotations

import os
import sys
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
import polars as pl
from tqdm import tqdm
import time

# Добавляем путь к app для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.yandex_sdk import embed_text
from app.config import get_settings


# Настройки
VACANCIES_PARQUET = "financial_coach/data/financial_vacancies.parquet"
EMBEDDINGS_DIR = "financial_coach/data/embeddings/vacancies"
BATCH_SIZE = 100  # Размер батча для обработки


def create_text_for_embedding(vacancy: Dict[str, Any]) -> str:
    """
    Создает текст для эмбеддинга из вакансии
    
    Объединяет название, описание и навыки для лучшего представления.
    
    Args:
        vacancy: Словарь с данными вакансии
        
    Returns:
        Текст для создания эмбеддинга
    """
    parts = []
    
    # Название
    if title := vacancy.get("title"):
        parts.append(f"Должность: {title}")
    
    # Описание (первые 1000 символов)
    if description := vacancy.get("description"):
        description = description[:1000] if len(description) > 1000 else description
        parts.append(f"Описание: {description}")
    
    # Навыки
    if skills := vacancy.get("key_skills"):
        parts.append(f"Навыки: {skills}")
    
    # Компания и локация
    if company := vacancy.get("company"):
        parts.append(f"Компания: {company}")
    if location := vacancy.get("location"):
        parts.append(f"Локация: {location}")
    
    return "\n".join(parts)


def generate_embeddings_for_vacancies(
    vacancies: List[Dict[str, Any]],
    output_dir: str,
    batch_size: int = BATCH_SIZE
) -> None:
    """
    Генерирует эмбеддинги для списка вакансий
    
    Args:
        vacancies: Список словарей с вакансиями
        output_dir: Директория для сохранения эмбеддингов
        batch_size: Размер батча для обработки
    """
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📊 Генерация эмбеддингов для {len(vacancies)} вакансий...")
    print(f"💾 Сохранение в: {output_dir}")
    
    # Проверяем уже существующие файлы для продолжения
    existing_files = list(Path(output_dir).glob("embeddings_batch_*.npy"))
    if existing_files:
        existing_nums = [int(f.stem.split("_")[-1]) for f in existing_files]
        last_batch = max(existing_nums)
        start_idx = last_batch * batch_size
        print(f"📂 Найдено {len(existing_files)} существующих батчей. Продолжаем с индекса {start_idx}")
    else:
        start_idx = 0
        last_batch = 0
    
    embeddings_list = []
    indices_list = []
    processed_count = 0
    
    # Обрабатываем вакансии батчами
    for i in tqdm(range(start_idx, len(vacancies), batch_size), desc="Обработка батчей"):
        batch = vacancies[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        # Проверяем, не существует ли уже этот батч
        embeddings_path = os.path.join(output_dir, f"embeddings_batch_{batch_num}.npy")
        if os.path.exists(embeddings_path):
            print(f"⏭️  Батч {batch_num} уже существует, пропускаем...")
            continue
        
        for vacancy in batch:
            try:
                # Создаем текст для эмбеддинга
                text = create_text_for_embedding(vacancy)
                
                # Генерируем эмбеддинг
                embedding = embed_text(text, model_kind="doc")
                
                # Сохраняем
                embeddings_list.append(embedding)
                indices_list.append(vacancy.get("idx", 0))
                processed_count += 1
                
                # Небольшая задержка между запросами
                time.sleep(0.1)
                
            except Exception as e:
                print(f"⚠️  Ошибка при обработке вакансии {vacancy.get('idx')}: {e}")
                continue
        
        # Сохраняем батч после обработки всех вакансий в батче
        if embeddings_list:
            try:
                embeddings_array = np.array(embeddings_list, dtype="float32")
                indices_array = np.array(indices_list, dtype="int32")
                
                # Сохраняем эмбеддинги
                indices_path = os.path.join(output_dir, f"indices_batch_{batch_num}.npy")
                
                # Сохраняем атомарно (сначала во временный файл, потом переименовываем)
                temp_emb_path = embeddings_path + ".tmp"
                temp_idx_path = indices_path + ".tmp"
                
                np.save(temp_emb_path, embeddings_array)
                np.save(temp_idx_path, indices_array)
                
                # Атомарное переименование
                os.rename(temp_emb_path, embeddings_path)
                os.rename(temp_idx_path, indices_path)
                
                print(f"✅ Сохранен батч {batch_num}: {len(embeddings_list)} эмбеддингов")
                
                # Очищаем списки для следующего батча
                embeddings_list = []
                indices_list = []
                
            except Exception as e:
                print(f"❌ Ошибка при сохранении батча {batch_num}: {e}")
                # Удаляем временные файлы при ошибке
                for temp_file in [embeddings_path + ".tmp", indices_path + ".tmp"]:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                raise
    
    print(f"🎉 Генерация завершена! Обработано {processed_count} вакансий")
    print(f"💾 Эмбеддинги сохранены в {output_dir}")


def main():
    """Главная функция"""
    print("="*60)
    print("🔍 ГЕНЕРАЦИЯ ЭМБЕДДИНГОВ ДЛЯ ФИНАНСОВЫХ ВАКАНСИЙ")
    print("="*60)
    print()
    
    # Проверяем наличие файла с вакансиями
    if not os.path.exists(VACANCIES_PARQUET):
        print(f"❌ Файл {VACANCIES_PARQUET} не найден!")
        print(f"📝 Сначала запустите скрипт парсинга:")
        print(f"   python data_parsing/scrape_financial_vacancies_hh.py")
        return
    
    # Проверяем настройки YandexGPT
    settings = get_settings()
    if not settings.yandex_folder_id or not (settings.yandex_api_key or settings.yandex_iam_token):
        print("❌ Не настроен YandexGPT!")
        print("📝 Укажите YANDEX_FOLDER_ID и YANDEX_API_KEY в файле .env")
        return
    
    # Загружаем вакансии
    print(f"📂 Загрузка вакансий из {VACANCIES_PARQUET}...")
    df = pl.read_parquet(VACANCIES_PARQUET)
    vacancies = df.to_dicts()
    
    print(f"✅ Загружено {len(vacancies)} вакансий")
    print()
    
    # Генерируем эмбеддинги
    generate_embeddings_for_vacancies(
        vacancies=vacancies,
        output_dir=EMBEDDINGS_DIR,
        batch_size=BATCH_SIZE
    )
    
    print()
    print("="*60)
    print("✅ ГОТОВО!")
    print("="*60)
    print()
    print("📝 Следующий шаг: запустите API для использования эмбеддингов")
    print("   python -m uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()














