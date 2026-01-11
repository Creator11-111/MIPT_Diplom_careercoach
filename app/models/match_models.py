"""
Модели для поиска вакансий и курсов

Эти модели определяют структуру запросов и ответов для поиска
подходящих вакансий и курсов для финансового специалиста.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MatchedVacancy(BaseModel):
    """Найденная вакансия"""
    model_config = ConfigDict(extra="forbid")
    
    idx: int
    title: Optional[str] = Field(default="")
    company: Optional[str] = Field(default="")
    location: Optional[str] = Field(default="")
    salary: Optional[str] = Field(default="")
    experience: Optional[str] = Field(default="")
    job_type: Optional[str] = Field(default="")
    description: Optional[str] = Field(default="")
    key_skills: Optional[str] = Field(default="")
    hh_url: Optional[str] = Field(default="", description="Ссылка на вакансию на HH.ru")
    seniority_level: Optional[str] = Field(default="", description="Уровень позиции: Стажер, Начальный, Средний, Продвинутый, Эксперт, Руководитель")


class MatchVacanciesResponse(BaseModel):
    """Ответ с найденными вакансиями"""
    model_config = ConfigDict(extra="forbid")
    
    top_idx: List[int] = Field(default_factory=list, description="Топ вакансий из FAISS")
    stage1: List[int] = Field(default_factory=list, description="Отобранные на этапе 1 (по названиям)")
    result: List[MatchedVacancy] = Field(default_factory=list, description="Финальный результат (по описаниям)")


class MatchVacanciesRequest(BaseModel):
    """Запрос на поиск вакансий"""
    model_config = ConfigDict(extra="forbid")
    
    resume: str = Field(description="Резюме или описание профиля финансового специалиста")
    k_faiss: int = Field(default=100, ge=1, le=2000, description="Количество вакансий из FAISS")
    k_stage1: int = Field(default=20, ge=1, le=200, description="Количество вакансий после этапа 1 (по названиям)")
    k_stage2: int = Field(default=15, ge=1, le=100, description="Количество вакансий после этапа 2 (по описаниям)")


class MatchVacanciesBySessionRequest(BaseModel):
    """Запрос на поиск вакансий по сессии (без резюме, резюме строится из профиля)"""
    model_config = ConfigDict(extra="forbid")
    
    k_faiss: int = Field(default=100, ge=1, le=2000, description="Количество вакансий из FAISS")
    k_stage1: int = Field(default=20, ge=1, le=200, description="Количество вакансий после этапа 1")
    k_stage2: int = Field(default=15, ge=1, le=100, description="Количество вакансий после этапа 2")


# ============================================================================
# МОДЕЛИ ДЛЯ КУРСОВ РАЗВИТИЯ
# ============================================================================

class MatchedCourse(BaseModel):
    """Найденный курс"""
    model_config = ConfigDict(extra="forbid")
    
    idx: int
    name: Optional[str] = Field(default="", description="Название курса")
    provider: Optional[str] = Field(default="", description="Провайдер курса (университет, платформа)")
    url: Optional[str] = Field(default="", description="Ссылка на курс")
    description: Optional[str] = Field(default="", description="Описание курса")
    skills: Optional[str] = Field(default="", description="Навыки, которые дает курс")
    level: Optional[str] = Field(default="", description="Уровень курса")
    duration: Optional[str] = Field(default="", description="Длительность курса")
    language: Optional[str] = Field(default="", description="Язык курса (например: Русский, English)")


class MatchCoursesRequest(BaseModel):
    """Запрос на поиск курсов для развития"""
    model_config = ConfigDict(extra="forbid")
    
    desired_skills: str = Field(description="Желаемые навыки или целевая позиция")
    field: Optional[str] = Field(default=None, description="Финансовая сфера")
    specialization: Optional[str] = Field(default=None, description="Специализация")
    k_faiss: int = Field(default=100, ge=1, le=2000, description="Количество курсов из FAISS")
    k_stage1: int = Field(default=20, ge=1, le=200, description="Количество курсов после этапа 1")
    k_stage2: int = Field(default=10, ge=1, le=100, description="Количество курсов после этапа 2")


class MatchCoursesResponse(BaseModel):
    """Ответ с найденными курсами"""
    model_config = ConfigDict(extra="forbid")
    
    top_idx: List[int] = Field(default_factory=list, description="Топ курсов из FAISS")
    stage1: List[int] = Field(default_factory=list, description="Отобранные на этапе 1")
    result: List[MatchedCourse] = Field(default_factory=list, description="Финальный результат")


class CareerDevelopmentRequest(BaseModel):
    """Запрос на развитие карьеры - курсы и вакансии для перехода к желаемой позиции"""
    model_config = ConfigDict(extra="forbid")
    
    session_id: str = Field(description="ID сессии пользователя")
    target_position: str = Field(description="Желаемая позиция (например: Финансовый директор)")
    target_field: Optional[str] = Field(default=None, description="Целевая сфера (если отличается от текущей)")
    target_specialization: Optional[str] = Field(default=None, description="Целевая специализация")


class CareerDevelopmentResponse(BaseModel):
    """Ответ с курсами и вакансиями для развития"""
    model_config = ConfigDict(extra="forbid")
    
    current_position: Optional[str] = Field(default=None, description="Текущая позиция пользователя")
    target_position: str = Field(description="Желаемая позиция")
    gap_analysis: Optional[str] = Field(default=None, description="Анализ разрыва между текущей и желаемой позицией")
    courses: List[MatchedCourse] = Field(default_factory=list, description="Рекомендуемые курсы")
    future_vacancies: List[MatchedVacancy] = Field(default_factory=list, description="Вакансии на пути к цели")
