"""
Сервис для построения профиля финансового специалиста из истории чата

Этот сервис анализирует всю историю диалога и создает структурированный профиль
с опытом работы, навыками, целями и предпочтениями.
"""

from __future__ import annotations

import json
from typing import List

from app.repos.chat_repos import SessionsRepository, MessagesRepository
from app.services.yandex_sdk import run_structured_completion
from app.prompts import PROFILE_SYSTEM_PROMPT


class ProfileService:
    """Сервис для построения профиля из истории чата"""
    
    def __init__(self) -> None:
        self._system_prompt = PROFILE_SYSTEM_PROMPT

    def get_profile_schema(self) -> dict:
        """
        Возвращает JSON-схему для профиля финансового специалиста
        
        Returns:
            Словарь с описанием схемы профиля
        """
        return {
            "json_schema": {
                "title": "Financial Professional Profile",
                "type": "object",
                "description": "Профиль финансового специалиста",
                "properties": {
                    "achievements": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Глобальные достижения пользователя в финансовой сфере",
                    },
                    "professional_context": {
                        "title": "Professional Context",
                        "type": "object",
                        "description": "Профессиональный контекст финансового специалиста",
                        "properties": {
                            "professional_field": {
                                "title": "Professional Field",
                                "type": "string",
                                "description": "Профессиональная область (Банки, Инвестиции, Аудит, Страхование, Финтеч)"
                            },
                            "specialization": {
                                "title": "Specialization",
                                "type": "string",
                                "description": "Специализация (Финансовый анализ, Риск-менеджмент, M&A, Кредитование и т.д.)"
                            },
                            "professional_role": {
                                "title": "Professional Role",
                                "type": "string",
                                "description": "Профессиональная роль (Финансовый аналитик, CFO, Банковский специалист и т.д.)"
                            },
                            "seniority_level": {
                                "title": "Seniority Level",
                                "type": "string",
                                "description": "Уровень (junior/middle/senior/lead/director)"
                            },
                        },
                    },
                    "resume": {
                        "title": "Resume",
                        "type": "array",
                        "description": "Опыт работы в финансовом секторе",
                        "items": {
                            "type": "object",
                            "properties": {
                                "company": {"type": "string", "description": "Компания"},
                                "title": {"type": "string", "description": "Должность"},
                                "start_date": {"type": "string"},
                                "end_date": {"type": ["string", "null"], "description": "Дата окончания (null если текущая)"},
                                "tasks": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Задачи и обязанности"
                                },
                                "achievements": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Достижения на работе"
                                },
                                "tech_stack": {
                                    "description": "Финансовые системы и технологии для этой работы (1С, SAP, Bloomberg и т.д.)",
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "tools": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Инструменты для этой работы (Excel, Python, SQL и т.д.)"
                                },
                            },
                        },
                    },
                    "skills": {
                        "title": "Skills",
                        "type": "object",
                        "description": "Навыки и образование финансового специалиста",
                        "properties": {
                            "hard_skills": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Финансовые навыки (финансовый анализ, МСФО, бюджетирование, риск-менеджмент)"
                            },
                            "soft_skills": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Soft skills (работа с клиентами, управление командой, презентации)"
                            },
                            "tools": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Инструменты (1С, SAP, Bloomberg Terminal, Excel, Python/R)"
                            },
                            "tech_stack": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Технологии и системы"
                            },
                            "certifications": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Профессиональные сертификаты (CFA, FRM, ACCA, CPA, CIMA)"
                            },
                            "education": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Образование (финансы, экономика, бухучет, MBA)"
                            },
                            "courses": {
                                "type": "array",
                                "title": "Courses",
                                "description": "Пройденные курсы в финансовой сфере",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "provider": {"type": "string"},
                                        "year": {"type": "integer"},
                                        "skills_gained": {"type": "array", "items": {"type": "string"}},
                                    },
                                },
                            },
                        },
                    },
                    "goals": {
                        "title": "Goals",
                        "type": "object",
                        "description": "Карьерные цели финансового специалиста",
                        "properties": {
                            "target_field": {
                                "title": "Target Field",
                                "type": "string",
                                "description": "Целевая область (Банки, Инвестиции, Аудит, Страхование, Финтеч)"
                            },
                            "target_specialization": {
                                "title": "Target Specialization",
                                "type": "string",
                                "description": "Целевая специализация (Финансовый анализ, Риск-менеджмент, M&A и т.д.)"
                            },
                            "desired_activities": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Желаемые виды деятельности (Аналитика, Управление, Консалтинг, Трейдинг)"
                            },
                            "desired_role": {
                                "title": "Desired Role",
                                "type": "string",
                                "description": "Желаемая роль (Финансовый аналитик, CFO, Инвестиционный менеджер и т.д.)"
                            },
                            "desired_level": {
                                "title": "Desired Level",
                                "type": "string",
                                "description": "Желаемый уровень (junior/middle/senior/lead/director)"
                            },
                            "salary_expectation": {
                                "type": "object",
                                "properties": {
                                    "currency": {"title": "Currency", "type": "string", "description": "Валюта (RUR, USD, EUR)"},
                                    "gross": {"title": "Gross", "type": "boolean", "description": "До вычета налогов"},
                                    "min": {"title": "Min", "type": "integer", "description": "Минимальная зарплата"},
                                    "max": {"title": "Max", "type": "integer", "description": "Максимальная зарплата"}
                                }
                            },
                        },
                    },
                    "preferences": {
                        "title": "Preferences",
                        "type": "object",
                        "description": "Предпочтения пользователя",
                        "properties": {
                            "work_format": {"enum": ["Remote", "Office", "Hybrid"]},
                            "location": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Города работы (Москва, Санкт-Петербург и т.д.)"
                            },
                        },
                    },
                },
            }
        }['json_schema']

    async def build_profile(
        self,
        session_id: str,
        sessions_repo: SessionsRepository,
        messages_repo: MessagesRepository
    ) -> dict:
        """
        Строит профиль финансового специалиста из истории чата
        
        Args:
            session_id: ID сессии
            sessions_repo: Репозиторий сессий
            messages_repo: Репозиторий сообщений
            
        Returns:
            Словарь с session_id и профилем
            
        Raises:
            ValueError: Если сессия не найдена или интервью не завершено
        """
        # Проверяем, что сессия существует
        session = await sessions_repo.find_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        # Проверяем, что интервью завершено
        # Получаем все сообщения для проверки
        all_msgs = await messages_repo.list_by_session(session_id, limit=1000)
        
        # Проверяем наличие сообщений
        if not all_msgs or len(all_msgs) < 4:
            raise ValueError(
                "Interview not finished: not enough messages. "
                "Please continue the conversation to complete the interview."
            )
        
        # Проверяем последнее сообщение ассистента
        last_msg = await messages_repo.find_last_assistant_message(session_id)
        
        # Более гибкая проверка: если есть достаточно сообщений (больше 10),
        # то можно попробовать построить профиль даже если done не установлен
        if not last_msg:
            raise ValueError(
                "Interview not finished: no assistant messages found. "
                "Please continue the conversation."
            )
        
        # Если done не установлен, но есть достаточно сообщений (больше 8), разрешаем построение профиля
        # (AI может не всегда корректно устанавливать done, или пользователь уже ответил на все вопросы)
        if not last_msg.get("done") and len(all_msgs) < 8:
            raise ValueError(
                "Interview not finished: not enough messages. "
                "Please continue the conversation to complete the interview."
            )

        # Получаем всю историю сообщений
        msgs = await messages_repo.list_by_session(session_id, limit=1000)
        chat_messages: List[dict] = [
            {"role": m["role"], "text": m["content"]} 
            for m in msgs
        ]
        
        # Строим список сообщений для YandexGPT
        messages = [{"role": "system", "text": self._system_prompt}] + chat_messages
        
        # Генерируем профиль через YandexGPT
        raw = run_structured_completion(
            messages,
            self.get_profile_schema(),
            max_tokens=8000
        )
        
        # Парсим результат
        try:
            data = json.loads(raw)
        except Exception as exc:
            raise ValueError("Failed to parse structured profile JSON") from exc
        
        return {"session_id": session_id, "profile": data}





