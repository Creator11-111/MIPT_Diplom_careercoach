#!/usr/bin/env python3
"""
Скрипт для оценки качества семантического поиска вакансий.

Запуск:
    python scripts/experiments/eval_retrieval.py

Требования:
    - Запущенный сервер (uvicorn app.main:app)
    - Переменные окружения (YANDEX_API_KEY, MONGO_URI)
    - Тестовый набор данных (scripts/experiments/test_profiles.json)

Метрики:
    - Precision@k
    - Recall@k
    - NDCG@k
    - MRR
"""

import json
import math
import time
from pathlib import Path
from typing import List, Dict, Any

import requests


# Конфигурация
API_BASE_URL = "http://localhost:8080"
K_VALUES = [5, 10, 15]


def load_test_profiles(path: str = "scripts/experiments/test_profiles.json") -> List[Dict]:
    """Загрузка тестовых профилей с разметкой релевантных вакансий."""
    if not Path(path).exists():
        print(f"⚠️ Файл {path} не найден. Создаём пример...")
        create_example_test_profiles(path)
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_example_test_profiles(path: str):
    """Создание примера тестового набора."""
    example = [
        {
            "profile_id": "test_1",
            "resume": "Финансовый аналитик с опытом 3 года в банке. Работал с МСФО, бюджетированием. Владею Excel, 1С, Python.",
            "relevant_idx": [101, 205, 312, 415, 520],  # Пример релевантных idx
            "description": "Middle финансовый аналитик, банковский сектор"
        },
        {
            "profile_id": "test_2", 
            "resume": "Риск-менеджер с опытом 5 лет в инвестиционной компании. CFA Level 2, знание Bloomberg Terminal.",
            "relevant_idx": [150, 275, 380, 490, 600],
            "description": "Senior риск-менеджер, инвестиции"
        },
        # Добавьте больше тестовых профилей...
    ]
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(example, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Создан пример тестового набора: {path}")
    print("⚠️ Отредактируйте файл и добавьте реальные релевантные idx вакансий")


def match_vacancies(resume: str) -> List[int]:
    """Вызов API для получения рекомендаций."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/v1/match/vacancies",
            json={"resume": resume},
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        return [v["idx"] for v in data.get("result", [])]
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        return []


def precision_at_k(retrieved: List[int], relevant: List[int], k: int) -> float:
    """Precision@k: доля релевантных среди первых k результатов."""
    if k == 0:
        return 0.0
    top_k = set(retrieved[:k])
    relevant_set = set(relevant)
    return len(top_k & relevant_set) / k


def recall_at_k(retrieved: List[int], relevant: List[int], k: int) -> float:
    """Recall@k: доля найденных релевантных от всех релевантных."""
    if len(relevant) == 0:
        return 0.0
    top_k = set(retrieved[:k])
    relevant_set = set(relevant)
    return len(top_k & relevant_set) / len(relevant_set)


def dcg_at_k(retrieved: List[int], relevant: List[int], k: int) -> float:
    """DCG@k: Discounted Cumulative Gain."""
    relevant_set = set(relevant)
    dcg = 0.0
    for i, idx in enumerate(retrieved[:k]):
        if idx in relevant_set:
            dcg += 1.0 / math.log2(i + 2)  # i+2 потому что i начинается с 0
    return dcg


def ndcg_at_k(retrieved: List[int], relevant: List[int], k: int) -> float:
    """NDCG@k: Normalized DCG."""
    dcg = dcg_at_k(retrieved, relevant, k)
    # Идеальный DCG: все релевантные на первых позициях
    ideal_k = min(k, len(relevant))
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_k))
    return dcg / idcg if idcg > 0 else 0.0


def mrr(retrieved: List[int], relevant: List[int]) -> float:
    """MRR: Mean Reciprocal Rank."""
    relevant_set = set(relevant)
    for i, idx in enumerate(retrieved):
        if idx in relevant_set:
            return 1.0 / (i + 1)
    return 0.0


def evaluate_profile(profile: Dict) -> Dict[str, Any]:
    """Оценка качества для одного профиля."""
    resume = profile["resume"]
    relevant = profile["relevant_idx"]
    
    print(f"  Профиль: {profile.get('description', profile['profile_id'])}")
    
    start_time = time.time()
    retrieved = match_vacancies(resume)
    latency = time.time() - start_time
    
    if not retrieved:
        print(f"    ⚠️ Нет результатов")
        return None
    
    results = {
        "profile_id": profile["profile_id"],
        "latency_s": latency,
        "retrieved_count": len(retrieved),
        "relevant_count": len(relevant),
    }
    
    for k in K_VALUES:
        results[f"precision@{k}"] = precision_at_k(retrieved, relevant, k)
        results[f"recall@{k}"] = recall_at_k(retrieved, relevant, k)
        results[f"ndcg@{k}"] = ndcg_at_k(retrieved, relevant, k)
    
    results["mrr"] = mrr(retrieved, relevant)
    
    print(f"    Precision@15: {results['precision@15']:.3f}, "
          f"NDCG@15: {results['ndcg@15']:.3f}, "
          f"MRR: {results['mrr']:.3f}, "
          f"Latency: {latency:.2f}s")
    
    return results


def aggregate_results(results: List[Dict]) -> Dict[str, float]:
    """Агрегация результатов по всем профилям."""
    if not results:
        return {}
    
    agg = {}
    metrics = [f"{m}@{k}" for m in ["precision", "recall", "ndcg"] for k in K_VALUES]
    metrics.append("mrr")
    metrics.append("latency_s")
    
    for metric in metrics:
        values = [r[metric] for r in results if r and metric in r]
        if values:
            agg[f"avg_{metric}"] = sum(values) / len(values)
    
    return agg


def main():
    print("=" * 60)
    print("ОЦЕНКА КАЧЕСТВА СЕМАНТИЧЕСКОГО ПОИСКА ВАКАНСИЙ")
    print("=" * 60)
    
    # Проверка доступности API
    try:
        health = requests.get(f"{API_BASE_URL}/health", timeout=5)
        health.raise_for_status()
        print(f"✅ API доступен: {API_BASE_URL}")
    except Exception as e:
        print(f"❌ API недоступен: {e}")
        print("   Запустите сервер: uvicorn app.main:app --port 8080")
        return
    
    # Загрузка тестовых профилей
    profiles = load_test_profiles()
    print(f"\n📊 Загружено {len(profiles)} тестовых профилей")
    
    # Оценка каждого профиля
    print("\n🔍 Оценка качества поиска:")
    results = []
    for profile in profiles:
        result = evaluate_profile(profile)
        if result:
            results.append(result)
    
    # Агрегация результатов
    print("\n" + "=" * 60)
    print("ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
    print("=" * 60)
    
    agg = aggregate_results(results)
    
    print(f"\nПротестировано профилей: {len(results)}/{len(profiles)}")
    print("\nМетрики качества:")
    for k in K_VALUES:
        print(f"  Precision@{k}: {agg.get(f'avg_precision@{k}', 0):.3f}")
        print(f"  Recall@{k}:    {agg.get(f'avg_recall@{k}', 0):.3f}")
        print(f"  NDCG@{k}:      {agg.get(f'avg_ndcg@{k}', 0):.3f}")
        print()
    
    print(f"  MRR:          {agg.get('avg_mrr', 0):.3f}")
    print(f"  Avg Latency:  {agg.get('avg_latency_s', 0):.2f}s")
    
    # Сохранение результатов
    output_path = "scripts/experiments/eval_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "profiles_count": len(profiles),
            "evaluated_count": len(results),
            "aggregate": agg,
            "details": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Результаты сохранены: {output_path}")


if __name__ == "__main__":
    main()
