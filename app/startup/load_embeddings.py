"""
Загрузка эмбеддингов и построение FAISS индексов для быстрого поиска

FAISS (Facebook AI Similarity Search) - библиотека для быстрого поиска похожих векторов.
Это позволяет находить релевантные вакансии по запросу пользователя за миллисекунды.

При запуске приложения:
1. Загружаются все эмбеддинги из файлов .npy
2. Строится FAISS индекс для быстрого поиска
3. Индекс хранится в памяти для мгновенного доступа
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import faiss  # type: ignore
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️  FAISS не установлен. Установите: pip install faiss-cpu")


# Определяем путь к папке с эмбеддингами
def _get_embeddings_dir() -> Path:
    """Определяет путь к папке с эмбеддингами вакансий"""
    # 1. Проверяем переменную окружения
    env_dir = os.environ.get("EMBEDDINGS_DIR")
    if env_dir:
        return Path(env_dir) / "vacancies"
    
    # 2. Проверяем Docker путь (если запущено в контейнере)
    docker_dir = Path("/app/embeddings/vacancies")
    if docker_dir.exists():
        return docker_dir
    
    # 3. Локальный путь (относительно этого файла)
    local_dir = Path(__file__).resolve().parents[2] / "data" / "embeddings" / "vacancies"
    return local_dir


VAC_EMBED_DIR = _get_embeddings_dir()

# Глобальные переменные для хранения индексов
if FAISS_AVAILABLE:
    faiss_index: Optional[faiss.Index] = None  # type: ignore
else:
    faiss_index: Optional[any] = None
vacancy_ids: list[int] = []  # Соответствие индекса в FAISS к idx вакансии


def _load_all_embeddings(dir_path: Path) -> tuple[np.ndarray, list[int]]:
    """
    Загружает все эмбеддинги из папки
    
    Эмбеддинги сохранены в формате батчей:
    - embeddings_batch_1.npy - массив эмбеддингов для батча
    - indices_batch_1.npy - массив idx вакансий для батча
    
    Args:
        dir_path: Путь к папке с .npy файлами
        
    Returns:
        Кортеж (массив эмбеддингов, список idx вакансий)
        
    Raises:
        FileNotFoundError: Если файлы не найдены
    """
    # Ищем все файлы с эмбеддингами батчей
    embedding_files = sorted(
        dir_path.glob("embeddings_batch_*.npy"),
        key=lambda x: int(x.stem.split("_")[-1])
    )
    
    if not embedding_files:
        raise FileNotFoundError(
            f"❌ Файлы эмбеддингов не найдены в {dir_path}\n"
            f"💡 Запустите: python data_parsing/generate_embeddings.py"
        )
    
    print(f"📂 Найдено {len(embedding_files)} батчей эмбеддингов")
    
    arrays = []
    ids = []
    
    for emb_file in embedding_files:
        try:
            # Загружаем эмбеддинги батча
            embeddings_batch = np.load(emb_file)
            
            # Загружаем соответствующие индексы
            batch_num = emb_file.stem.split("_")[-1]
            indices_file = dir_path / f"indices_batch_{batch_num}.npy"
            
            if indices_file.exists():
                indices_batch = np.load(indices_file)
            else:
                # Если файл с индексами не найден, создаем последовательные индексы
                print(f"⚠️  Файл {indices_file.name} не найден, используем последовательные индексы")
                indices_batch = np.arange(len(embeddings_batch))
            
            # Добавляем в общие списки
            # embeddings_batch должен быть массивом формы (N, dim), где N - количество эмбеддингов в батче
            # indices_batch должен быть массивом формы (N,)
            
            # Нормализуем форму embeddings_batch
            if len(embeddings_batch.shape) == 1:
                # Если это один эмбеддинг (1D массив), делаем его двумерным
                embeddings_batch = embeddings_batch.reshape(1, -1)
            
            # Нормализуем форму indices_batch
            if not isinstance(indices_batch, np.ndarray):
                indices_batch = np.array([indices_batch])
            elif len(indices_batch.shape) == 0:
                # Скаляр
                indices_batch = np.array([indices_batch])
            
            # Проверяем соответствие размеров
            num_embeddings = embeddings_batch.shape[0]
            num_indices = indices_batch.shape[0]
            
            if num_embeddings != num_indices:
                print(f"⚠️  Несоответствие размеров в батче {batch_num}: {num_embeddings} эмбеддингов, {num_indices} индексов")
                # Берем минимум
                min_size = min(num_embeddings, num_indices)
                embeddings_batch = embeddings_batch[:min_size]
                indices_batch = indices_batch[:min_size]
            
            # Добавляем в общие списки
            arrays.append(embeddings_batch)
            ids.extend(indices_batch.flatten().tolist())
                
        except Exception as e:
            print(f"⚠️  Ошибка загрузки {emb_file.name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if not arrays:
        raise ValueError("Не удалось загрузить ни одного эмбеддинга")
    
    # Объединяем все массивы в один
    X = np.vstack(arrays)
    print(f"✅ Загружено {len(ids)} эмбеддингов из {len(arrays)} батчей, размерность: {X.shape}")
    
    return X, ids


def build_faiss() -> None:
    """
    Строит FAISS индекс для быстрого поиска похожих вакансий
    
    Этот индекс позволяет находить похожие вакансии за миллисекунды,
    используя семантический поиск по эмбеддингам.
    """
    global faiss_index, vacancy_ids
    
    if not FAISS_AVAILABLE:
        print("⚠️  FAISS не установлен. Поиск по эмбеддингам недоступен.")
        print("💡 Установите: pip install faiss-cpu")
        return
    
    if not VAC_EMBED_DIR.exists():
        print(f"⚠️  Папка с эмбеддингами не найдена: {VAC_EMBED_DIR}")
        print("💡 Запустите генерацию эмбеддингов: python data_parsing/generate_embeddings.py")
        print("💡 Приложение будет работать без FAISS индекса (поиск будет медленнее)")
        faiss_index = None
        vacancy_ids = []
        return
    
    try:
        print(f"🔍 Построение FAISS индекса из {VAC_EMBED_DIR}...")
        
        # Загружаем все эмбеддинги
        X, ids = _load_all_embeddings(VAC_EMBED_DIR)
        
        if len(ids) == 0:
            print("⚠️  Не удалось загрузить эмбеддинги")
            faiss_index = None
            vacancy_ids = []
            return
        
        # Нормализуем векторы (делаем их единичной длины)
        # Это улучшает качество поиска
        norms = np.linalg.norm(X, axis=1, keepdims=True) + 1e-12
        X_normalized = X / norms
        
        # Создаем FAISS индекс
        # IndexHNSWFlat - быстрый и точный алгоритм для поиска
        dim = X_normalized.shape[1]
        if not FAISS_AVAILABLE:
            print("⚠️  FAISS не установлен. Установите: pip install faiss-cpu")
            faiss_index = None
            vacancy_ids = []
            return
            
        index = faiss.IndexHNSWFlat(dim, 32)  # 32 - параметр для баланса скорости/точности
        index.hnsw.efConstruction = 200  # Параметр качества построения
        
        # Добавляем все векторы в индекс
        print("💾 Добавление векторов в индекс...")
        index.add(X_normalized.astype('float32'))
        
        faiss_index = index
        vacancy_ids = ids
        
        print(f"✅ FAISS индекс построен: {len(ids)} вакансий")
        print(f"   Размерность векторов: {dim}")
        
    except FileNotFoundError as e:
        print(f"⚠️  {e}")
        print("💡 Приложение будет работать без FAISS индекса (поиск будет медленнее)")
        faiss_index = None
        vacancy_ids = []
    except Exception as e:
        print(f"⚠️  Ошибка построения FAISS индекса: {e}")
        print("💡 Приложение будет работать без FAISS индекса (поиск будет медленнее)")
        faiss_index = None
        vacancy_ids = []


def search_top_k(query_vec: np.ndarray, k: int = 10) -> list[int]:
    """
    Поиск топ-K похожих вакансий по эмбеддингу запроса
    
    Args:
        query_vec: Эмбеддинг запроса пользователя (1D массив)
        k: Количество вакансий для возврата
        
    Returns:
        Список idx вакансий, отсортированных по релевантности
        
    Raises:
        RuntimeError: Если индекс не построен
    """
    if not FAISS_AVAILABLE:
        raise RuntimeError("FAISS не установлен. Установите: pip install faiss-cpu")
    
    if faiss_index is None:
        raise RuntimeError("FAISS индекс не построен. Вызовите build_faiss() сначала.")
    
    if len(vacancy_ids) == 0:
        raise RuntimeError("Список ID вакансий пуст.")
    
    # Нормализуем вектор запроса
    query_norm = np.linalg.norm(query_vec)
    if query_norm > 0:
        query_normalized = (query_vec / query_norm).astype('float32').reshape(1, -1)
    else:
        raise ValueError("Вектор запроса не может быть нулевым")
    
    # Ищем k ближайших соседей
    if not FAISS_AVAILABLE or faiss_index is None:
        raise RuntimeError("FAISS индекс недоступен")
    distances, indices = faiss_index.search(query_normalized, min(k, len(vacancy_ids)))
    
    # Преобразуем индексы FAISS в idx вакансий
    result_ids = [vacancy_ids[int(idx)] for idx in indices[0] if 0 <= int(idx) < len(vacancy_ids)]
    
    return result_ids


def get_index_stats() -> dict[str, any]:
    """
    Получить статистику по индексу
    
    Returns:
        Словарь со статистикой
    """
    return {
        "index_built": faiss_index is not None,
        "vacancies_count": len(vacancy_ids),
        "embeddings_dir": str(VAC_EMBED_DIR),
        "faiss_available": FAISS_AVAILABLE,
    }

