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
    
    @property
    def port(self) -> int:
        """Порт для запуска приложения (приоритет: PORT > APP_PORT > 8000)"""
        import os
        return int(os.getenv("PORT", os.getenv("APP_PORT", self.app_port)))

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

    # CORS настройки
    cors_origins: str = Field(
        default="*",
        alias="CORS_ORIGINS",
        description="Comma-separated list of allowed origins. Use '*' for all (not recommended for production)"
    )

    # Rate limiting (опционально)
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, alias="RATE_LIMIT_WINDOW")  # seconds

    def get_cors_origins_list(self) -> list[str]:
        """Получить список разрешенных CORS origins"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def validate_required(self) -> None:
        """Валидация обязательных настроек"""
        errors = []
        
        if not self.yandex_folder_id:
            errors.append("YANDEX_FOLDER_ID is required")
        if not self.yandex_api_key and not self.yandex_iam_token:
            errors.append("Either YANDEX_API_KEY or YANDEX_IAM_TOKEN is required")
        if not self.mongo_uri or self.mongo_uri == "mongodb://localhost:27017":
            if self.app_env == "production":
                errors.append("MONGO_URI must be set for production")
        
        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Получение настроек (кэшируется для производительности)
    
    Returns:
        Объект Settings с настройками приложения
    """
    return Settings()  # type: ignore[call-arg]















