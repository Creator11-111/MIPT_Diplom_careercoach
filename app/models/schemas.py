"""
Схемы данных для финансового карьерного коуча

Эти модели определяют структуру данных, которые используются в API.
Все модели адаптированы для финансового и банковского сектора.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional, List
from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# МОДЕЛИ ДЛЯ ЧАТА И СЕССИЙ
# ============================================================================

class MessageRole(str, Enum):
    """Роли участников диалога"""
    user = "user"
    assistant = "assistant"
    system = "system"


class Message(BaseModel):
    """Модель сообщения в чате"""
    model_config = ConfigDict(extra="forbid")
    
    message_id: str
    session_id: str
    role: MessageRole
    content: str
    created_at: str
    tokens: Optional[int] = None
    done: Optional[bool] = None  # Завершено ли интервью


class SessionState(BaseModel):
    """Состояние сессии"""
    model_config = ConfigDict(extra="forbid")
    
    last_question_type: Optional[
        Literal["experience", "skills", "education", "goals", "preferences", "summary", "generic"]
    ] = None
    last_updated_at: str


class Session(BaseModel):
    """Сессия диалога с пользователем"""
    model_config = ConfigDict(extra="forbid")
    
    session_id: str
    user_id: str
    state: SessionState


class CreateSessionRequest(BaseModel):
    """Запрос на создание новой сессии"""
    model_config = ConfigDict(extra="forbid")
    
    user_id: Optional[str] = None


class CreateSessionResponse(BaseModel):
    """Ответ с ID созданной сессии"""
    model_config = ConfigDict(extra="forbid")
    
    session_id: str
    user_id: Optional[str] = None


class GetSessionResponse(BaseModel):
    """Получение сессии с сообщениями"""
    model_config = ConfigDict(extra="forbid")
    
    session: Session
    messages: List[Message]


class SessionListItem(BaseModel):
    """Элемент списка сессий"""
    model_config = ConfigDict(extra="forbid")
    
    session_id: str
    user_id: str
    last_updated_at: str
    preview: Optional[str] = None  # Превью последнего сообщения


class ListSessionsResponse(BaseModel):
    """Список сессий пользователя"""
    model_config = ConfigDict(extra="forbid")
    
    sessions: List[SessionListItem]


class ChatRequest(BaseModel):
    """Запрос на отправку сообщения в чат"""
    model_config = ConfigDict(extra="forbid")
    
    text: str


class ChatResponse(BaseModel):
    """Ответ от AI ассистента"""
    model_config = ConfigDict(extra="forbid")
    
    session_id: str
    reply: str
    done: bool  # Завершено ли интервью


class HealthResponse(BaseModel):
    """Ответ для проверки работоспособности API"""
    model_config = ConfigDict(extra="forbid")
    
    status: Literal["ok"]
    time: str


# ============================================================================
# МОДЕЛИ ДЛЯ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ (ФИНАНСОВЫЙ СЕКТОР)
# ============================================================================

class CourseItem(BaseModel):
    """Курс, пройденный пользователем"""
    model_config = ConfigDict(extra="forbid")
    
    title: Optional[str] = None  # Название курса
    provider: Optional[str] = None  # Провайдер (например, Coursera, Нетология)
    year: Optional[int] = None  # Год прохождения
    skills_gained: List[str] = []  # Полученные навыки


class ResumeItem(BaseModel):
    """Опыт работы в финансовом секторе"""
    model_config = ConfigDict(extra="forbid")
    
    company: Optional[str] = Field(
        default=None, 
        description="Компания, в которой работал пользователь (банк, инвестиционная компания и т.д.)"
    )
    title: Optional[str] = Field(
        default=None, 
        description="Должность пользователя (Финансовый аналитик, CFO и т.д.)"
    )
    start_date: Optional[str] = None
    end_date: Optional[str] = Field(
        default=None, 
        description="Дата окончания работы (None если текущее место работы)"
    )
    tasks: List[str] = Field(
        default_factory=list, 
        description="Задачи, которые выполнялись на работе (финансовый анализ, бюджетирование и т.д.)"
    )
    achievements: List[str] = Field(
        default_factory=list, 
        description="Достижения на работе"
    )
    tech_stack: List[str] = Field(
        default_factory=list, 
        description="Финансовые системы и инструменты (1С, SAP, Bloomberg, Excel/VBA и т.д.)"
    )
    tools: List[str] = Field(
        default_factory=list, 
        description="Инструменты на конкретной работе"
    )


class ProfessionalContext(BaseModel):
    """Профессиональный контекст финансового специалиста"""
    model_config = ConfigDict(extra="forbid")
    
    professional_field: Optional[str] = Field(
        default=None, 
        description="Профессиональная область (Банки, Инвестиции, Аудит, Страхование, Финтеч)"
    )
    specialization: Optional[str] = Field(
        default=None, 
        description="Специализация (Финансовый анализ, Риск-менеджмент, M&A, Кредитование и т.д.)"
    )
    professional_role: Optional[str] = Field(
        default=None, 
        description="Профессиональная роль (Финансовый аналитик, CFO, Банковский специалист и т.д.)"
    )
    seniority_level: Optional[str] = Field(
        default=None,
        description="Уровень (junior/middle/senior/lead/director)"
    )


class Skills(BaseModel):
    """Навыки финансового специалиста"""
    model_config = ConfigDict(extra="forbid")
    
    hard_skills: List[str] = Field(
        default_factory=list, 
        description="Hard skills (Финансовый анализ, МСФО, Бюджетирование, Риск-менеджмент и т.д.)"
    )
    soft_skills: List[str] = Field(
        default_factory=list, 
        description="Soft skills (Коммуникация, Управление командой, Презентации и т.д.)"
    )
    tools: List[str] = Field(
        default_factory=list, 
        description="Инструменты (1С:Бухгалтерия, SAP, Bloomberg Terminal, Excel, Python/R для финансов)"
    )
    tech_stack: List[str] = Field(
        default_factory=list, 
        description="Финансовые системы и технологии"
    )
    courses: List[CourseItem] = Field(
        default_factory=list, 
        description="Курсы и полученные навыки"
    )
    certifications: List[str] = Field(
        default_factory=list,
        description="Профессиональные сертификаты (CFA, FRM, ACCA, CPA, CIMA и т.д.)"
    )
    education: List[str] = Field(
        default_factory=list,
        description="Образование (финансы, экономика, бухучет, MBA)"
    )


class SalaryExpectation(BaseModel):
    """Ожидания по зарплате"""
    model_config = ConfigDict(extra="forbid")
    
    currency: Optional[str] = Field(default=None, description="Валюта (RUR, USD, EUR)")
    gross: Optional[bool] = Field(default=None, description="До вычета налогов (gross)")
    min: Optional[int] = Field(default=None, description="Минимальная зарплата")
    max: Optional[int] = Field(default=None, description="Максимальная зарплата")


class Goals(BaseModel):
    """Карьерные цели финансового специалиста"""
    model_config = ConfigDict(extra="forbid")
    
    target_field: Optional[str] = Field(
        default=None, 
        description="Целевая область (Банки, Инвестиции, Аудит, Страхование, Финтеч)"
    )
    target_specialization: Optional[str] = Field(
        default=None, 
        description="Целевая специализация (Финансовый анализ, Риск-менеджмент, M&A и т.д.)"
    )
    desired_activities: List[str] = Field(
        default_factory=list,
        description="Желаемые виды деятельности (Аналитика, Управление, Консалтинг, Трейдинг)"
    )
    desired_role: Optional[str] = Field(
        default=None, 
        description="Желаемая роль (Финансовый аналитик, CFO, Инвестиционный менеджер и т.д.)"
    )
    desired_level: Optional[str] = Field(
        default=None, 
        description="Желаемый уровень (junior/middle/senior/lead/director)"
    )
    salary_expectation: Optional[SalaryExpectation] = None


class Preferences(BaseModel):
    """Предпочтения по работе"""
    model_config = ConfigDict(extra="forbid")
    
    work_format: Optional[Literal["Remote", "Office", "Hybrid"]] = None
    location: List[str] = Field(
        default_factory=list, 
        description="Города работы (Москва, Санкт-Петербург и т.д.)"
    )


class UserProfile(BaseModel):
    """Полный профиль финансового специалиста"""
    model_config = ConfigDict(extra="forbid")
    
    achievements: List[str] = Field(
        default_factory=list, 
        description="Глобальные достижения пользователя"
    )
    professional_context: Optional[ProfessionalContext] = Field(
        default=None, 
        description="Профессиональный контекст пользователя"
    )
    resume: List[ResumeItem] = Field(
        default_factory=list, 
        description="Опыт работы в финансовом секторе"
    )
    skills: Optional[Skills] = Field(
        default=None, 
        description="Навыки и образование пользователя"
    )
    goals: Optional[Goals] = Field(
        default=None, 
        description="Карьерные цели пользователя"
    )
    preferences: Optional[Preferences] = Field(
        default=None, 
        description="Предпочтения пользователя"
    )


class ProfileResponse(BaseModel):
    """Ответ с профилем пользователя"""
    model_config = ConfigDict(extra="forbid")
    
    session_id: str
    profile: UserProfile










