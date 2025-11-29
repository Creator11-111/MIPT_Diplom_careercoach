"""
Конфигурация приложения финансового карьерного коуча

Этот файл содержит все настройки приложения:
- Подключение к базе данных MongoDB
- API ключи для YandexGPT
- Настройки сервера

ВСЕ СЕКРЕТНЫЕ ДАННЫЕ (API ключи) хранятся в файле .env
"""

from __future__ import annotations

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Настройки приложения
    
    Все значения читаются из переменных окружения или файла .env
    """
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=False
    )

    # Настройки приложения
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")

    # Настройки MongoDB (база данных)
    mongo_uri: str = Field(default="mongodb://localhost:27017", alias="MONGO_URI")
    mongo_db: str = Field(default="financial_career_coach", alias="MONGO_DB")

    # Настройки YandexGPT (обязательно для работы!)
    yandex_folder_id: str = Field(default="", alias="YANDEX_FOLDER_ID")
    yandex_api_key: str = Field(default="", alias="YANDEX_API_KEY")
    yandex_iam_token: str = Field(default="", alias="YANDEX_IAM_TOKEN")

    # Настройки чата
    message_window_size: int = Field(default=40, alias="MESSAGE_WINDOW_SIZE")

    # JWT для аутентификации (опционально)
    backend_jwt_secret: str = Field(default="", alias="BACKEND_JWT_SECRET")
    backend_jwt_algorithm: str = Field(default="HS256", alias="BACKEND_JWT_ALGORITHM")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Получение настроек (кэшируется для производительности)
    
    Returns:
        Объект Settings с настройками приложения
    """
    return Settings()  # type: ignore[call-arg]













