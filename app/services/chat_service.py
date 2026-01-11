"""
Chat service for user interaction and interview management.

Responsibilities:
- AI response generation via YandexGPT
- Financial professional profile data collection through structured interview
- Interview completion state determination
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import List, Tuple

from app.models import Message, MessageRole, ChatResponse
from app.prompts import (
    CHAT_SYSTEM_PROMPT,
    CAREER_DEVELOPMENT_CHAT_PROMPT,
    SKILLS_ANALYSIS_CHAT_PROMPT,
    GOALS_ANALYSIS_CHAT_PROMPT,
)
from app.services.yandex_sdk import run_structured_completion
from app.repos.chat_repos import SessionsRepository, MessagesRepository
from app.repos.profile_repos import ProfilesRepository


class ChatService:
    """Chat processing service for interview and conversation management."""
    
    def __init__(self) -> None:
        self._system_prompt = CHAT_SYSTEM_PROMPT

    def build_messages_payload(
        self, 
        chat_messages: List[dict], 
        profile_exists: bool = False,
        chat_type: str | None = None
    ) -> List[dict]:
        """
        Строит список сообщений для отправки в YandexGPT
        
        Args:
            chat_messages: Список сообщений из базы данных
            profile_exists: Существует ли профиль пользователя
            chat_type: Тип чата ('Развитие карьеры', 'Анализ навыков', 'Анализ целей')
            
        Returns:
            Список сообщений в формате для YandexGPT
        """
        # Выбираем промпт в зависимости от типа чата и наличия профиля
        if profile_exists and chat_type:
            if chat_type == 'Развитие карьеры':
                system_prompt = CAREER_DEVELOPMENT_CHAT_PROMPT
            elif chat_type == 'Анализ навыков':
                system_prompt = SKILLS_ANALYSIS_CHAT_PROMPT
            elif chat_type == 'Анализ целей':
                system_prompt = GOALS_ANALYSIS_CHAT_PROMPT
            else:
                system_prompt = self._system_prompt
        else:
            system_prompt = self._system_prompt
        
        messages: List[dict] = [{"role": "system", "text": system_prompt}]
        messages.extend([{"role": m["role"], "text": m["content"]} for m in chat_messages])
        return messages

    def get_response_schema(self) -> dict:
        """
        Возвращает JSON-схему для ответа от YandexGPT
        
        Returns:
            Словарь с описанием схемы ответа
        """
        return {
            "title": "Chat Response",
            "description": "Схема для ответа AI в чате",
            "type": "object",
            "properties": {
                "answer_to_user2": {
                    "title": "Ответ пользователю",
                    "type": "string",
                    "description": "Ответ AI на вопрос пользователя"
                },
                "done": {
                    "title": "Завершено",
                    "type": "boolean",
                    "description": "Вся ли нужная информация о финансовом специалисте собрана"
                },
            },
            "required": ["answer_to_user2", "done"],
        }

    def parse_model_output(self, raw: str) -> Tuple[str, bool]:
        """
        Парсит ответ от YandexGPT
        
        Args:
            raw: Сырой ответ от модели
            
        Returns:
            Кортеж (текст ответа, завершено ли интервью)
        """
        if not raw or not raw.strip():
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Empty response from YandexGPT")
            return "Извините, произошла ошибка при генерации ответа. Пожалуйста, попробуйте еще раз.", False
        
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to parse JSON from YandexGPT: {e}, raw: {raw[:200]}")
            # Пытаемся извлечь текст даже если JSON невалидный
            if "answer_to_user2" in raw:
                import re
                match = re.search(r'"answer_to_user2"\s*:\s*"([^"]*)"', raw)
                if match:
                    return match.group(1), False
            return "Извините, произошла ошибка при обработке ответа. Пожалуйста, попробуйте еще раз.", False
        
        reply_text = data.get("answer_to_user2", "").strip()
        if not reply_text:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Empty reply_text in response: {data}")
            return "Извините, не удалось получить ответ. Пожалуйста, попробуйте еще раз.", False
        
        done = bool(data.get("done", False))
        return reply_text, done

    async def generate_welcome_message(
        self,
        session_id: str,
        sessions_repo: SessionsRepository,
        messages_repo: MessagesRepository,
    ) -> ChatResponse:
        """
        Генерирует приветственное сообщение для новой сессии
        
        Args:
            session_id: ID сессии
            sessions_repo: Репозиторий сессий
            messages_repo: Репозиторий сообщений
            
        Returns:
            ChatResponse с приветственным сообщением
        """
        # Проверяем, что сессия существует
        session = await sessions_repo.find_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        # Проверяем, есть ли уже сообщения в сессии
        existing_messages = await messages_repo.list_by_session(session_id, limit=1)
        if existing_messages:
            # Если сообщения уже есть, возвращаем последнее
            last_msg = existing_messages[0]
            return ChatResponse(
                session_id=session_id,
                reply=last_msg.get("content", ""),
                done=last_msg.get("done", False)
            )

        # Генерируем приветственное сообщение через YandexGPT
        # Используем специальный промпт для первого сообщения
        messages = [{"role": "system", "text": self._system_prompt}]
        messages.append({
            "role": "user",
            "text": "Здравствуйте! Я готов начать интервью."
        })
        
        try:
            raw = run_structured_completion(messages, self.get_response_schema())
            if not raw:
                import logging
                logger = logging.getLogger(__name__)
                logger.error("Empty response from run_structured_completion for welcome message")
                raise ValueError("Failed to get welcome message from AI")
            reply_text, done = self.parse_model_output(raw)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating welcome message: {e}", exc_info=True)
            raise ValueError(f"Failed to generate welcome message: {str(e)}") from e

        # Сохраняем приветственное сообщение
        now = datetime.utcnow().isoformat()
        assistant_msg = Message(
            message_id=now + ":assistant",
            session_id=session_id,
            role=MessageRole.assistant,
            content=reply_text,
            created_at=now,
            tokens=None,
            done=done,
        )
        await messages_repo.insert_one(assistant_msg.model_dump())

        return ChatResponse(session_id=session_id, reply=reply_text, done=done)

    async def generate_reply(
        self,
        session_id: str,
        text: str,
        sessions_repo: SessionsRepository,
        messages_repo: MessagesRepository,
        profiles_repo: ProfilesRepository | None = None,
    ) -> ChatResponse:
        """
        Генерирует ответ AI на сообщение пользователя
        
        Args:
            session_id: ID сессии
            text: Текст сообщения пользователя
            sessions_repo: Репозиторий сессий
            messages_repo: Репозиторий сообщений
            
        Returns:
            ChatResponse с ответом AI
            
        Raises:
            ValueError: Если сессия не найдена
        """
        # Проверяем, что сессия существует
        session = await sessions_repo.find_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        # Сохраняем сообщение пользователя
        now = datetime.utcnow().isoformat()
        user_msg = Message(
            message_id=now + ":user",
            session_id=session_id,
            role=MessageRole.user,
            content=text,
            created_at=now,
            tokens=None,
        )
        await messages_repo.insert_one(user_msg.model_dump())

        # Проверяем наличие профиля и определяем тип чата
        profile_exists = False
        chat_type = None
        profile_info = None
        
        if profiles_repo:
            try:
                # Пробуем найти профиль по session_id
                profile_doc = await profiles_repo.find_by_session_id(session_id)
                if profile_doc:
                    profile_exists = True
                    profile_info = profile_doc.get("profile", {})
                else:
                    # Пробуем найти по user_id
                    session = await sessions_repo.find_by_id(session_id)
                    if session and session.get("user_id"):
                        profile_doc = await profiles_repo.find_by_user_id(session["user_id"])
                        if profile_doc:
                            profile_exists = True
                            profile_info = profile_doc.get("profile", {})
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error checking profile: {e}")
        
        # Определяем тип чата по всем сообщениям
        all_msgs = await messages_repo.list_by_session(session_id, limit=50)
        if all_msgs:
            # Проверяем все сообщения для определения типа чата
            for msg in all_msgs:
                content = msg.get("content", "").lower()
                if "развитие карьеры" in content or "план развития" in content or "начало работы в разделе: развитие карьеры" in content:
                    chat_type = "Развитие карьеры"
                    break
                elif "анализ навыков" in content or ("навыки" in content and "анализ" in content) or "начало работы в разделе: анализ навыков" in content:
                    chat_type = "Анализ навыков"
                    break
                elif "анализ целей" in content or "карьерные цели" in content or "начало работы в разделе: анализ целей" in content:
                    chat_type = "Анализ целей"
                    break
        
        # Получаем последние сообщения для контекста
        last_msgs = await messages_repo.list_by_session(session_id, limit=40)
        
        # Если есть профиль и это специальный раздел, добавляем информацию о профиле в промпт
        if profile_exists and profile_info and chat_type:
            # Формируем краткую информацию о профиле для контекста
            profile_summary = []
            if profile_info.get("professional_context"):
                pc = profile_info["professional_context"]
                if pc.get("professional_role"):
                    profile_summary.append(f"Текущая позиция: {pc['professional_role']}")
                if pc.get("professional_field"):
                    profile_summary.append(f"Сфера: {pc['professional_field']}")
            if profile_info.get("skills"):
                sk = profile_info["skills"]
                if sk.get("hard_skills"):
                    profile_summary.append(f"Навыки: {', '.join(sk['hard_skills'][:10])}")
            
            if profile_summary:
                # Модифицируем системный промпт, добавляя информацию о профиле
                enhanced_prompt = f"{CAREER_DEVELOPMENT_CHAT_PROMPT if chat_type == 'Развитие карьеры' else (SKILLS_ANALYSIS_CHAT_PROMPT if chat_type == 'Анализ навыков' else GOALS_ANALYSIS_CHAT_PROMPT)}\n\nИНФОРМАЦИЯ ИЗ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ (уже известна, не спрашивай про это):\n" + "\n".join(profile_summary)
                messages = [{"role": "system", "text": enhanced_prompt}]
                messages.extend([{"role": m["role"], "text": m["content"]} for m in last_msgs])
            else:
                messages = self.build_messages_payload(last_msgs, profile_exists, chat_type)
        else:
            messages = self.build_messages_payload(last_msgs, profile_exists, chat_type)
        
        # Генерируем ответ через YandexGPT
        try:
            raw = run_structured_completion(messages, self.get_response_schema())
            if not raw:
                import logging
                logger = logging.getLogger(__name__)
                logger.error("Empty response from run_structured_completion")
                raise ValueError("Failed to get response from AI")
            reply_text, done = self.parse_model_output(raw)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating reply: {e}", exc_info=True)
            raise ValueError(f"Failed to generate reply: {str(e)}") from e

        # Сохраняем ответ AI
        assistant_msg = Message(
            message_id=now + ":assistant",
            session_id=session_id,
            role=MessageRole.assistant,
            content=reply_text,
            created_at=now,
            tokens=None,
            done=done,
        )
        await messages_repo.insert_one(assistant_msg.model_dump())

        return ChatResponse(session_id=session_id, reply=reply_text, done=done)





