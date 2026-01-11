"""
Embedding loading and FAISS index construction for vector similarity search.

FAISS (Facebook AI Similarity Search) provides efficient approximate nearest neighbor
search for high-dimensional vectors.
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
    print("⚠️ FAISS не установлен. Установите: pip install faiss-cpu")


def _get_embeddings_dir() -> Path:
    """Returns path to vacancy embeddings directory."""
    # Check paths in priority order
    paths_to_check = [
        # Docker path (Cloud Run)
        Path("/app/data/embeddings/vacancies"),
        # Alternative Docker path
        Path("/app/embeddings/vacancies"),
        # Local path (relative to this file)
        Path(__file__).resolve().parents[2] / "data" / "embeddings" / "vacancies",
    ]
    
    # Environment variable (highest priority)
    env_dir = os.environ.get("EMBEDDINGS_DIR")
    if env_dir:
        paths_to_check.insert(0, Path(env_dir) / "vacancies")
    
    for path in paths_to_check:
        if path.exists():
            # Проверяем есть ли файлы эмбеддингов
            embedding_files = list(path.glob("embeddings_batch_*.npy"))
            if embedding_files:
                print(f"✅ Found embeddings: {path} ({len(embedding_files)} batches)")
                return path
    
    # Ничего не найдено - возвращаем Docker путь для логирования
    print(f"⚠️ Embeddings not found. Checked paths:")
    for p in paths_to_check:
        print(f"   - {p} (exists: {p.exists()})")
    return paths_to_check[0]


VAC_EMBED_DIR = _get_embeddings_dir()

# Глобальные переменные для хранения индексов
if FAISS_AVAILABLE:
    faiss_index: Optional[faiss.Index] = None  # type: ignore
else:
    faiss_index: Optional[any] = None
vacancy_ids: list[int] = []


def _load_all_embeddings(dir_path: Path) -> tuple[np.ndarray, list[int]]:
    """Загружает все эмбеддинги из папки"""
    
    # Ищем все файлы с эмбеддингами
    embedding_files = sorted(
        dir_path.glob("embeddings_batch_*.npy"),
        key=lambda x: int(x.stem.split("_")[-1])
    )
    
    if not embedding_files:
        raise FileNotFoundError(f"No embedding files in {dir_path}")
    
    print(f"📂 Loading {len(embedding_files)} embedding batches...")
    
    arrays = []
    ids = []
    
    for emb_file in embedding_files:
        try:
            # Загружаем эмбеддинги
            embeddings_batch = np.load(emb_file)
            
            # Загружаем индексы
            batch_num = emb_file.stem.split("_")[-1]
            indices_file = dir_path / f"indices_batch_{batch_num}.npy"
            
            if indices_file.exists():
                indices_batch = np.load(indices_file)
            else:
                # Создаем последовательные индексы
                indices_batch = np.arange(len(embeddings_batch))
            
            # Нормализуем форму
            if len(embeddings_batch.shape) == 1:
                embeddings_batch = embeddings_batch.reshape(1, -1)
            
            if not isinstance(indices_batch, np.ndarray):
                indices_batch = np.array([indices_batch])
            elif len(indices_batch.shape) == 0:
                indices_batch = np.array([indices_batch.item()])
            
            # Проверяем соответствие размеров
            min_size = min(embeddings_batch.shape[0], len(indices_batch.flatten()))
            embeddings_batch = embeddings_batch[:min_size]
            indices_batch = indices_batch.flatten()[:min_size]
            
            arrays.append(embeddings_batch)
            ids.extend(indices_batch.tolist())
            
        except Exception as e:
            print(f"⚠️ Error loading {emb_file.name}: {e}")
            continue
    
    if not arrays:
        raise ValueError("No embeddings loaded")
    
    X = np.vstack(arrays)
    print(f"✅ Loaded {len(ids)} embeddings, dimension: {X.shape[1]}")
    
    return X, ids


def build_faiss() -> None:
    """Строит FAISS индекс для быстрого поиска похожих вакансий"""
    global faiss_index, vacancy_ids
    
    if not FAISS_AVAILABLE:
        print("⚠️ FAISS not available")
        faiss_index = None
        vacancy_ids = []
        return
    
    if not VAC_EMBED_DIR.exists():
        print(f"⚠️ Embeddings directory not found: {VAC_EMBED_DIR}")
        faiss_index = None
        vacancy_ids = []
        return
    
    try:
        print(f"🔍 Building FAISS index from {VAC_EMBED_DIR}...")
        
        # Загружаем эмбеддинги
        X, ids = _load_all_embeddings(VAC_EMBED_DIR)
        
        if len(ids) == 0:
            print("⚠️ No embeddings loaded")
            faiss_index = None
            vacancy_ids = []
            return
        
        # Нормализуем векторы
        norms = np.linalg.norm(X, axis=1, keepdims=True) + 1e-12
        X_normalized = X / norms
        
        # Создаем FAISS индекс
        dim = X_normalized.shape[1]
        index = faiss.IndexHNSWFlat(dim, 32)
        index.hnsw.efConstruction = 200
        
        # Добавляем векторы
        print("💾 Adding vectors to index...")
        index.add(X_normalized.astype('float32'))
        
        faiss_index = index
        vacancy_ids = ids
        
        print(f"✅ FAISS index built: {len(ids)} vacancies, dim={dim}")
        
    except Exception as e:
        print(f"❌ FAISS build error: {e}")
        import traceback
        traceback.print_exc()
        faiss_index = None
        vacancy_ids = []


def search_top_k(query_vec: np.ndarray, k: int = 10) -> list[int]:
    """Поиск топ-K похожих вакансий по эмбеддингу запроса"""
    
    if not FAISS_AVAILABLE:
        raise RuntimeError("FAISS not installed")
    
    if faiss_index is None:
        raise RuntimeError("FAISS index not built. Check embeddings are loaded.")
    
    if len(vacancy_ids) == 0:
        raise RuntimeError("No vacancies in index")
    
    # Нормализуем вектор запроса
    query_norm = np.linalg.norm(query_vec)
    if query_norm == 0:
        raise ValueError("Query vector cannot be zero")
    
    query_normalized = (query_vec / query_norm).astype('float32').reshape(1, -1)
    
    # Ищем ближайших соседей
    distances, indices = faiss_index.search(query_normalized, min(k, len(vacancy_ids)))
    
    # Преобразуем индексы FAISS в idx вакансий
    result_ids = [vacancy_ids[int(idx)] for idx in indices[0] if 0 <= int(idx) < len(vacancy_ids)]
    
    return result_ids


def get_index_stats() -> dict[str, any]:
    """Получить статистику по индексу"""
    return {
        "index_built": faiss_index is not None,
        "vacancies_count": len(vacancy_ids),
        "embeddings_dir": str(VAC_EMBED_DIR),
        "faiss_available": FAISS_AVAILABLE,
    }
