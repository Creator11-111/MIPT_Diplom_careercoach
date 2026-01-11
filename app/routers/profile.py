"""
Роутер для работы с профилями пользователей

Профиль строится из истории чата после завершения интервью.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.db.mongo import get_db
from app.models import ProfileResponse
from app.repos.chat_repos import SessionsRepository, MessagesRepository
from app.repos.profile_repos import ProfilesRepository
from app.services.profile_service import ProfileService


router = APIRouter()


def get_profile_service() -> ProfileService:
    """Получить сервис профилей"""
    return ProfileService()


async def get_sessions_repo(db=Depends(get_db)) -> SessionsRepository:  # noqa: ANN001
    """Получить репозиторий сессий"""
    return SessionsRepository(db)


async def get_messages_repo(db=Depends(get_db)) -> MessagesRepository:  # noqa: ANN001
    """Получить репозиторий сообщений"""
    return MessagesRepository(db)


async def get_profiles_repo(db=Depends(get_db)) -> ProfilesRepository:  # noqa: ANN001
    """Получить репозиторий профилей"""
    return ProfilesRepository(db)


@router.get("/by-user/{user_id}", response_model=ProfileResponse)
async def get_profile_by_user_id(
    user_id: str,
    profiles_repo: ProfilesRepository = Depends(get_profiles_repo),
) -> ProfileResponse:
    """
    Получить профиль пользователя по user_id (из любой сессии)
    
    Args:
        user_id: ID пользователя
        profiles_repo: Репозиторий профилей
        
    Returns:
        ProfileResponse с профилем пользователя
        
    Raises:
        HTTPException: Если профиль не найден
    """
    existing_profile = await profiles_repo.find_by_user_id(user_id)
    if not existing_profile:
        raise HTTPException(status_code=404, detail="Profile not found for this user")
    
    from app.models import UserProfile
    return ProfileResponse(
        session_id=existing_profile.get("session_id", ""),
        profile=UserProfile.model_validate(existing_profile.get("profile", {}))
    )


@router.get("/{session_id}", response_model=ProfileResponse)
async def get_profile(
    session_id: str,
    service: ProfileService = Depends(get_profile_service),
    sessions_repo: SessionsRepository = Depends(get_sessions_repo),
    messages_repo: MessagesRepository = Depends(get_messages_repo),
    profiles_repo: ProfilesRepository = Depends(get_profiles_repo),
) -> ProfileResponse:
    """
    Получить профиль пользователя по session_id
    
    Если профиль еще не построен, он будет создан из истории чата.
    Профиль строится только после завершения интервью (done: true).
    
    Args:
        session_id: ID сессии
        service: Сервис профилей
        sessions_repo: Репозиторий сессий
        messages_repo: Репозиторий сообщений
        profiles_repo: Репозиторий профилей
        
    Returns:
        ProfileResponse с профилем пользователя
        
    Raises:
        HTTPException: Если сессия не найдена или интервью не завершено
    """
    try:
        # Пытаемся получить существующий профиль
        session = await sessions_repo.find_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Проверяем, есть ли уже сохраненный профиль
        existing_profile = await profiles_repo.find_by_session_id(session_id)
        if existing_profile:
            from app.models import UserProfile
            return ProfileResponse(
                session_id=session_id,
                profile=UserProfile.model_validate(existing_profile.get("profile", {}))
            )
        
        # Строим профиль из истории чата
        result = await service.build_profile(session_id, sessions_repo, messages_repo)
        
        # Сохраняем профиль в базу данных
        user_id = session.get("user_id", "")
        profile_data = {
            "user_id": user_id,
            "session_id": session_id,
            "profile": result["profile"]
        }
        await profiles_repo.upsert_one(profile_data)
        
        # Логируем для отладки
        print(f"✅ Профиль сохранен для сессии {session_id}, user_id: {user_id}")
        
        # Возвращаем профиль
        from app.models import UserProfile
        return ProfileResponse(
            session_id=session_id,
            profile=UserProfile.model_validate(result["profile"])
        )
        
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        elif "not finished" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=error_msg + " Please complete the interview first."
            )
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build profile: {e}")

