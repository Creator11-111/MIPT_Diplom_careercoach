"""
Роутер для обработки сообщений в чате

Этот роутер обрабатывает сообщения пользователя и возвращает ответы AI.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.db.mongo import get_db
from app.models import ChatResponse, ChatRequest
from app.repos.chat_repos import SessionsRepository, MessagesRepository
from app.services.chat_service import ChatService


router = APIRouter()


def get_chat_service() -> ChatService:
    """Получить сервис чата"""
    return ChatService()


async def get_sessions_repo(db=Depends(get_db)) -> SessionsRepository:  # noqa: ANN001
    """Получить репозиторий сессий"""
    return SessionsRepository(db)


async def get_messages_repo(db=Depends(get_db)) -> MessagesRepository:  # noqa: ANN001
    """Получить репозиторий сообщений"""
    return MessagesRepository(db)


@router.post("/{session_id}", response_model=ChatResponse)
async def chat(
    session_id: str,
    req: ChatRequest,
    service: ChatService = Depends(get_chat_service),
    sessions_repo: SessionsRepository = Depends(get_sessions_repo),
    messages_repo: MessagesRepository = Depends(get_messages_repo),
) -> ChatResponse:
    """
    Отправить сообщение в чат и получить ответ AI
    
    Args:
        session_id: ID сессии
        req: Запрос с текстом сообщения
        service: Сервис чата
        sessions_repo: Репозиторий сессий
        messages_repo: Репозиторий сообщений
        
    Returns:
        ChatResponse с ответом AI
        
    Raises:
        HTTPException: Если сессия не найдена или произошла ошибка
    """
    try:
        return await service.generate_reply(
            session_id, 
            req.text, 
            sessions_repo, 
            messages_repo
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404 if "Session not found" in str(e) else 400, 
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {e}")





