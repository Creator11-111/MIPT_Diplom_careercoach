"""
Интеграция с YandexGPT для финансового карьерного коуча

Этот модуль содержит функции для работы с YandexGPT:
- Генерация текста (чат, анализ)
- Создание эмбеддингов (для поиска похожих вакансий)
- Структурированный вывод (JSON ответы)
"""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List
from yandex_cloud_ml_sdk import YCloudML

from app.config import get_settings


def _get_sdk() -> YCloudML:
    """
    Получение SDK для работы с YandexGPT
    
    Returns:
        YCloudML объект для работы с YandexGPT
        
    Raises:
        RuntimeError: Если не указан folder_id или API ключ
    """
    settings = get_settings()
    if not settings.yandex_folder_id:
        raise RuntimeError("YANDEX_FOLDER_ID is required")
    auth = settings.yandex_api_key or settings.yandex_iam_token
    if not auth:
        raise RuntimeError("YANDEX_API_KEY or YANDEX_IAM_TOKEN is required")
    return YCloudML(folder_id=settings.yandex_folder_id, auth=auth)


def run_structured_completion(
    messages: List[Dict[str, str]],
    json_schema: Dict[str, Any],
    model_name: str = "yandexgpt",
    model_version: str = "rc",
    max_tokens: int = 1000,
) -> str:
    """
    Запрос к YandexGPT с структурированным выводом (JSON)
    
    Используется когда нужен ответ в определенном формате (например, профиль пользователя).
    
    Args:
        messages: Список сообщений для диалога
        json_schema: JSON схема для структурированного ответа
        model_name: Название модели (по умолчанию "yandexgpt")
        model_version: Версия модели (по умолчанию "rc")
        max_tokens: Максимальное количество токенов в ответе
        
    Returns:
        JSON строка с ответом модели
    """
    sdk = _get_sdk()
    model = sdk.models.completions(model_name, model_version=model_version)
    model = model.configure(response_format={"json_schema": json_schema}, max_tokens=max_tokens)
    result = model.run(messages)
    return result[0].text


def run_text_completion(
    messages: List[Dict[str, str]],
    model_name: str = "yandexgpt",
    model_version: str = "rc",
) -> str:
    """
    Обычный текстовый запрос к YandexGPT
    
    Используется когда нужен просто текст (например, ответ в чате).
    
    Args:
        messages: Список сообщений для диалога
        model_name: Название модели
        model_version: Версия модели
        
    Returns:
        Текст ответа модели
    """
    sdk = _get_sdk()
    model = sdk.models.completions(model_name, model_version=model_version)
    result = model.run(messages)
    return result[0].text


def get_embeddings_model(model_kind: str = "doc"):
    """
    Получение модели для создания эмбеддингов
    
    Args:
        model_kind: Тип модели ("doc" для документов, "query" для запросов)
        
    Returns:
        Модель для создания эмбеддингов
    """
    sdk = _get_sdk()
    return sdk.models.text_embeddings(model_kind)


def embed_text(text: str, model_kind: str = "query") -> np.ndarray:
    """
    Создание эмбеддинга текста
    
    Эмбеддинг - это вектор чисел, который представляет смысл текста.
    Похожие тексты имеют похожие эмбеддинги.
    
    Args:
        text: Текст для преобразования в эмбеддинг
        model_kind: Тип модели ("doc" для документов, "query" для запросов)
        
    Returns:
        NumPy массив с эмбеддингом (вектор чисел)
    """
    model = get_embeddings_model(model_kind)
    vec = model.run(text)
    return np.array(vec, dtype="float32")












