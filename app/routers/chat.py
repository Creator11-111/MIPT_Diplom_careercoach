"""
Роутер для обработки сообщений в чате

Этот роутер обрабатывает сообщения пользователя и возвращает ответы AI.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.db.mongo import get_db
from app.models import ChatResponse, ChatRequest
from app.repos.chat_repos import SessionsRepository, MessagesRepository
from app.repos.profile_repos import ProfilesRepository
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


async def get_profiles_repo(db=Depends(get_db)) -> ProfilesRepository:  # noqa: ANN001
    """Получить репозиторий профилей"""
    return ProfilesRepository(db)


@router.post("/{session_id}", response_model=ChatResponse)
async def chat(
    session_id: str,
    req: ChatRequest,
    service: ChatService = Depends(get_chat_service),
    sessions_repo: SessionsRepository = Depends(get_sessions_repo),
    messages_repo: MessagesRepository = Depends(get_messages_repo),
    profiles_repo: ProfilesRepository = Depends(get_profiles_repo),
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
    import logging
    logger = logging.getLogger(__name__)
    
    # Валидация входных данных
    if not session_id or not session_id.strip():
        raise HTTPException(status_code=400, detail="Session ID is required")
    
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Message text cannot be empty")
    
    if len(req.text) > 5000:
        raise HTTPException(status_code=400, detail="Message text is too long (max 5000 characters)")
    
    try:
        logger.info(f"Processing chat message for session {session_id[:8]}...")
        
        response = await service.generate_reply(
            session_id, 
            req.text.strip(), 
            sessions_repo, 
            messages_repo,
            profiles_repo
        )
        
        logger.info(f"Successfully generated reply for session {session_id[:8]}...")
        return response
        
    except ValueError as e:
        error_msg = str(e)
        logger.warning(f"Chat error (ValueError): {error_msg}")
        status_code = 404 if "Session not found" in error_msg else 400
        raise HTTPException(status_code=status_code, detail=error_msg)
    except RuntimeError as e:
        error_msg = str(e)
        logger.error(f"Chat error (RuntimeError - likely API issue): {error_msg}")
        if "API key" in error_msg or "UNAUTHENTICATED" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="AI service is temporarily unavailable. Please try again later."
            )
        raise HTTPException(status_code=503, detail="AI service error. Please try again later.")
    except Exception as e:
        logger.error(f"Chat failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred. Please try again later."
        )





