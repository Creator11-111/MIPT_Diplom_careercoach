#!/usr/bin/env python3
"""
Скрипт для измерения латентности и производительности системы.

Запуск:
    python scripts/experiments/benchmark_latency.py

Измеряемые операции:
    - Health check
    - FAISS search (через match_vacancies)
    - Chat message
    - Build profile
    - Career development

Метрики:
    - p50, p95, p99, max латентность
    - Throughput (RPS)
    - Error rate
"""

import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

import requests


# Конфигурация
API_BASE_URL = "http://localhost:8080"
NUM_ITERATIONS = 10
CONCURRENT_USERS = [1, 5, 10]


def measure_endpoint(
    method: str,
    endpoint: str,
    payload: Dict = None,
    iterations: int = NUM_ITERATIONS
) -> Dict[str, Any]:
    """Измерение латентности для одного эндпоинта."""
    latencies = []
    errors = 0
    
    for i in range(iterations):
        try:
            start = time.time()
            
            if method == "GET":
                response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=60)
            else:
                response = requests.post(
                    f"{API_BASE_URL}{endpoint}",
                    json=payload,
                    timeout=60
                )
            
            latency = time.time() - start
            
            if response.status_code == 200:
                latencies.append(latency)
            else:
                errors += 1
                print(f"    ⚠️ HTTP {response.status_code}")
                
        except Exception as e:
            errors += 1
            print(f"    ❌ Error: {e}")
    
    if not latencies:
        return {
            "endpoint": endpoint,
            "error_rate": 1.0,
            "p50": None,
            "p95": None,
            "p99": None,
            "max": None
        }
    
    latencies.sort()
    n = len(latencies)
    
    return {
        "endpoint": endpoint,
        "iterations": iterations,
        "successful": n,
        "errors": errors,
        "error_rate": errors / iterations,
        "p50": latencies[int(n * 0.5)] if n > 0 else None,
        "p95": latencies[int(n * 0.95)] if n >= 20 else (latencies[-1] if n > 0 else None),
        "p99": latencies[int(n * 0.99)] if n >= 100 else (latencies[-1] if n > 0 else None),
        "max": max(latencies) if latencies else None,
        "min": min(latencies) if latencies else None,
        "avg": statistics.mean(latencies) if latencies else None,
    }


def concurrent_benchmark(
    method: str,
    endpoint: str,
    payload: Dict,
    concurrent_users: int,
    duration_seconds: int = 30
) -> Dict[str, Any]:
    """Нагрузочное тестирование с параллельными запросами."""
    results = []
    errors = 0
    start_time = time.time()
    
    def single_request():
        try:
            req_start = time.time()
            if method == "GET":
                response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=60)
            else:
                response = requests.post(
                    f"{API_BASE_URL}{endpoint}",
                    json=payload,
                    timeout=60
                )
            return {
                "latency": time.time() - req_start,
                "status": response.status_code
            }
        except Exception as e:
            return {"latency": None, "status": 500, "error": str(e)}
    
    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = []
        while time.time() - start_time < duration_seconds:
            future = executor.submit(single_request)
            futures.append(future)
            time.sleep(0.1)  # Небольшая пауза между запросами
        
        for future in as_completed(futures):
            result = future.result()
            if result["latency"] is not None and result["status"] == 200:
                results.append(result["latency"])
            else:
                errors += 1
    
    total_time = time.time() - start_time
    total_requests = len(results) + errors
    
    if not results:
        return {
            "concurrent_users": concurrent_users,
            "duration_s": total_time,
            "total_requests": total_requests,
            "rps": 0,
            "error_rate": 1.0
        }
    
    results.sort()
    n = len(results)
    
    return {
        "concurrent_users": concurrent_users,
        "duration_s": total_time,
        "total_requests": total_requests,
        "successful_requests": n,
        "errors": errors,
        "rps": n / total_time,
        "error_rate": errors / total_requests if total_requests > 0 else 0,
        "p50": results[int(n * 0.5)],
        "p95": results[int(n * 0.95)] if n >= 20 else results[-1],
        "avg": statistics.mean(results),
    }


def main():
    print("=" * 60)
    print("BENCHMARK ЛАТЕНТНОСТИ И ПРОИЗВОДИТЕЛЬНОСТИ")
    print("=" * 60)
    
    # Проверка доступности API
    try:
        health = requests.get(f"{API_BASE_URL}/health", timeout=5)
        health.raise_for_status()
        print(f"✅ API доступен: {API_BASE_URL}")
    except Exception as e:
        print(f"❌ API недоступен: {e}")
        return
    
    results = {}
    
    # 1. Health check
    print("\n📊 Измерение: Health check")
    results["health"] = measure_endpoint("GET", "/health")
    print(f"   p50: {results['health']['p50']*1000:.1f}ms")
    
    # 2. Ready check (включает проверку FAISS)
    print("\n📊 Измерение: Ready check")
    results["ready"] = measure_endpoint("GET", "/ready")
    print(f"   p50: {results['ready']['p50']*1000:.1f}ms")
    
    # 3. Match vacancies (полный pipeline)
    print("\n📊 Измерение: Match vacancies (full pipeline)")
    test_resume = """
    Финансовый аналитик с опытом 3 года в банковском секторе.
    Работал с МСФО, бюджетированием, финансовым моделированием.
    Владею Excel, 1С:Бухгалтерия, Python, SQL.
    Образование: МГУ, экономический факультет.
    """
    results["match_vacancies"] = measure_endpoint(
        "POST",
        "/v1/match/vacancies",
        {"resume": test_resume},
        iterations=5  # Меньше итераций из-за высокой латентности
    )
    if results["match_vacancies"]["p50"]:
        print(f"   p50: {results['match_vacancies']['p50']:.2f}s")
        print(f"   p95: {results['match_vacancies']['p95']:.2f}s")
    
    # 4. Нагрузочное тестирование
    print("\n📊 Нагрузочное тестирование (Match vacancies):")
    results["load_test"] = {}
    
    for users in CONCURRENT_USERS:
        print(f"\n   Concurrent users: {users}")
        load_result = concurrent_benchmark(
            "POST",
            "/v1/match/vacancies",
            {"resume": test_resume},
            concurrent_users=users,
            duration_seconds=15
        )
        results["load_test"][f"users_{users}"] = load_result
        print(f"   RPS: {load_result['rps']:.2f}")
        print(f"   p95: {load_result.get('p95', 'N/A')}")
        print(f"   Error rate: {load_result['error_rate']*100:.1f}%")
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
    print("=" * 60)
    
    print("\n| Операция | p50 | p95 | p99 | Max |")
    print("|----------|-----|-----|-----|-----|")
    
    for name, data in results.items():
        if name == "load_test":
            continue
        if data.get("p50"):
            if data["p50"] < 1:
                print(f"| {name} | {data['p50']*1000:.0f}ms | "
                      f"{data.get('p95', data['p50'])*1000:.0f}ms | "
                      f"{data.get('p99', data['p50'])*1000:.0f}ms | "
                      f"{data['max']*1000:.0f}ms |")
            else:
                print(f"| {name} | {data['p50']:.2f}s | "
                      f"{data.get('p95', data['p50']):.2f}s | "
                      f"{data.get('p99', data['p50']):.2f}s | "
                      f"{data['max']:.2f}s |")
    
    print("\n| Concurrent Users | RPS | p95 Latency | Error Rate |")
    print("|------------------|-----|-------------|------------|")
    for key, data in results.get("load_test", {}).items():
        print(f"| {data['concurrent_users']} | {data['rps']:.2f} | "
              f"{data.get('p95', 0):.2f}s | {data['error_rate']*100:.1f}% |")
    
    # Сохранение результатов
    output_path = "scripts/experiments/benchmark_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "api_url": API_BASE_URL,
            "results": results
        }, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n✅ Результаты сохранены: {output_path}")


if __name__ == "__main__":
    main()
