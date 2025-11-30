"""
Сервис для обработки чата с пользователем

Этот сервис отвечает за:
- Генерацию ответов AI на вопросы пользователя
- Сбор информации о финансовом специалисте через интервью
- Определение завершенности интервью
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import List, Tuple

from app.models import Message, MessageRole, ChatResponse
from app.prompts import CHAT_SYSTEM_PROMPT
from app.services.yandex_sdk import run_structured_completion
from app.repos.chat_repos import SessionsRepository, MessagesRepository


class ChatService:
    """Сервис для обработки чата"""
    
    def __init__(self) -> None:
        self._system_prompt = CHAT_SYSTEM_PROMPT

    def build_messages_payload(self, chat_messages: List[dict]) -> List[dict]:
        """
        Строит список сообщений для отправки в YandexGPT
        
        Args:
            chat_messages: Список сообщений из базы данных
            
        Returns:
            Список сообщений в формате для YandexGPT
        """
        messages: List[dict] = [{"role": "system", "text": self._system_prompt}]
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
        try:
            data = json.loads(raw)
        except Exception:
            return "", False
        reply_text = data.get("answer_to_user2", "")
        done = bool(data.get("done", False))
        return reply_text, done

    async def generate_reply(
        self,
        session_id: str,
        text: str,
        sessions_repo: SessionsRepository,
        messages_repo: MessagesRepository,
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

        # Получаем последние сообщения для контекста
        last_msgs = await messages_repo.list_by_session(session_id, limit=40)
        messages = self.build_messages_payload(last_msgs)
        
        # Генерируем ответ через YandexGPT
        raw = run_structured_completion(messages, self.get_response_schema())
        reply_text, done = self.parse_model_output(raw)

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





