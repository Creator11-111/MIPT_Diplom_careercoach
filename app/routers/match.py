"""
Роутер для поиска подходящих вакансий

Использует профиль пользователя или текст резюме для поиска
наиболее подходящих финансовых вакансий.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.db.mongo import get_db
from app.models.match_models import (
    MatchVacanciesRequest,
    MatchVacanciesBySessionRequest,
    MatchVacanciesResponse,
    CareerDevelopmentRequest,
    CareerDevelopmentResponse,
)
from app.repos.vacancy_repos import VacanciesRepository
from app.repos.profile_repos import ProfilesRepository
from app.repos.course_repos import CoursesRepository
from app.services.match_service import MatchService
from app.services.career_development_service import CareerDevelopmentService


router = APIRouter()


def get_match_service() -> MatchService:
    """Получить сервис поиска вакансий"""
    return MatchService()


async def get_vacancies_repo(db=Depends(get_db)) -> VacanciesRepository:  # noqa: ANN001
    """Получить репозиторий вакансий"""
    return VacanciesRepository(db)


async def get_profiles_repo(db=Depends(get_db)) -> ProfilesRepository:  # noqa: ANN001
    """Получить репозиторий профилей"""
    return ProfilesRepository(db)


async def get_courses_repo(db=Depends(get_db)) -> CoursesRepository:  # noqa: ANN001
    """Получить репозиторий курсов"""
    return CoursesRepository(db)


def get_career_development_service() -> CareerDevelopmentService:
    """Получить сервис развития карьеры"""
    return CareerDevelopmentService()


@router.post("/vacancies", response_model=MatchVacanciesResponse)
async def match_vacancies(
    request: MatchVacanciesRequest,
    service: MatchService = Depends(get_match_service),
    vacancies_repo: VacanciesRepository = Depends(get_vacancies_repo),
) -> MatchVacanciesResponse:
    """
    Поиск подходящих вакансий для финансового специалиста
    
    Процесс поиска:
    1. Препроцессинг резюме (обогащение финансовыми ключевыми словами)
    2. Семантический поиск через FAISS (по эмбеддингам)
    3. Фильтрация по названиям вакансий через LLM
    4. Финальная фильтрация по описаниям через LLM
    
    Args:
        request: Запрос с резюме и параметрами поиска
        service: Сервис поиска вакансий
        vacancies_repo: Репозиторий вакансий
        
    Returns:
        MatchVacanciesResponse с найденными вакансиями
        
    Raises:
        HTTPException: Если произошла ошибка при поиске
    """
    try:
        return await service.match_vacancies(request, vacancies_repo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to match vacancies: {e}")


@router.post("/vacancies/by-session/{session_id}", response_model=MatchVacanciesResponse)
async def match_vacancies_by_session(
    session_id: str,
    request: MatchVacanciesBySessionRequest,
    service: MatchService = Depends(get_match_service),
    vacancies_repo: VacanciesRepository = Depends(get_vacancies_repo),
    profiles_repo: ProfilesRepository = Depends(get_profiles_repo),
) -> MatchVacanciesResponse:
    """
    Поиск вакансий на основе профиля из сессии
    
    Автоматически строит резюме из профиля пользователя и ищет вакансии.
    
    Args:
        session_id: ID сессии
        request: Запрос с параметрами поиска (resume будет проигнорирован)
        service: Сервис поиска вакансий
        vacancies_repo: Репозиторий вакансий
        profiles_repo: Репозиторий профилей
        
    Returns:
        MatchVacanciesResponse с найденными вакансиями
        
    Raises:
        HTTPException: Если профиль не найден или произошла ошибка
    """
    try:
        # Получаем профиль из сессии
        profile_doc = await profiles_repo.find_by_session_id(session_id)
        if not profile_doc:
            raise HTTPException(
                status_code=404,
                detail="Profile not found. Please complete the interview and build profile first."
            )
        
        # Строим текст резюме из профиля
        from app.models import UserProfile
        profile = UserProfile.model_validate(profile_doc.get("profile", {}))
        
        # Формируем резюме из профиля для поиска
        resume_parts = []
        
        # Профессиональный контекст
        if profile.professional_context:
            if profile.professional_context.professional_role:
                resume_parts.append(f"Профессиональная роль: {profile.professional_context.professional_role}")
            if profile.professional_context.professional_field:
                resume_parts.append(f"Сфера: {profile.professional_context.professional_field}")
            if profile.professional_context.specialization:
                resume_parts.append(f"Специализация: {profile.professional_context.specialization}")
            if profile.professional_context.seniority_level:
                resume_parts.append(f"Уровень: {profile.professional_context.seniority_level}")
        
        # Опыт работы
        if profile.resume:
            resume_parts.append("\nОпыт работы в финансовом секторе:")
            for item in profile.resume:
                job_desc = []
                if item.title:
                    job_desc.append(item.title)
                if item.company:
                    job_desc.append(f"в {item.company}")
                if job_desc:
                    resume_parts.append(f"- {' '.join(job_desc)}")
                
                if item.tasks:
                    resume_parts.append(f"  Задачи: {', '.join(item.tasks[:5])}")  # Первые 5 задач
                if item.tech_stack:
                    resume_parts.append(f"  Финансовые системы: {', '.join(item.tech_stack)}")
                if item.tools:
                    resume_parts.append(f"  Инструменты: {', '.join(item.tools)}")
        
        # Навыки
        if profile.skills:
            if profile.skills.hard_skills:
                resume_parts.append(f"\nФинансовые навыки: {', '.join(profile.skills.hard_skills)}")
            if profile.skills.tools:
                resume_parts.append(f"Инструменты: {', '.join(profile.skills.tools)}")
            if profile.skills.tech_stack:
                resume_parts.append(f"Технологии: {', '.join(profile.skills.tech_stack)}")
            if profile.skills.certifications:
                resume_parts.append(f"Сертификаты: {', '.join(profile.skills.certifications)}")
        
        # Достижения
        if profile.achievements:
            resume_parts.append(f"\nДостижения: {', '.join(profile.achievements[:3])}")
        
        resume_text = "\n".join(resume_parts)
        
        # Если резюме пустое, создаем базовое описание
        if not resume_text.strip():
            resume_text = "Финансовый специалист ищущий работу в финансовом секторе"
        
        # Создаем новый запрос с резюме из профиля
        new_request = MatchVacanciesRequest(
            resume=resume_text,
            k_faiss=request.k_faiss,
            k_stage1=request.k_stage1,
            k_stage2=request.k_stage2,
        )
        
        print(f"📝 Резюме для поиска (первые 200 символов): {resume_text[:200]}...")
        print(f"🔍 Параметры поиска: k_faiss={request.k_faiss}, k_stage1={request.k_stage1}, k_stage2={request.k_stage2}")
        
        return await service.match_vacancies(new_request, vacancies_repo)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to match vacancies: {e}")


@router.post("/career-development", response_model=CareerDevelopmentResponse)
async def get_career_development(
    request: CareerDevelopmentRequest,
    service: CareerDevelopmentService = Depends(get_career_development_service),
    profiles_repo: ProfilesRepository = Depends(get_profiles_repo),
    vacancies_repo: VacanciesRepository = Depends(get_vacancies_repo),
    courses_repo: CoursesRepository = Depends(get_courses_repo),
) -> CareerDevelopmentResponse:
    """
    Получить план развития карьеры: курсы и вакансии для перехода к желаемой позиции
    
    Процесс:
    1. Анализирует разрыв между текущей и желаемой позицией
    2. Находит курсы для развития необходимых навыков
    3. Находит вакансии на пути к цели (после прохождения курсов)
    
    Args:
        request: Запрос с session_id и целевой позицией
        service: Сервис развития карьеры
        profiles_repo: Репозиторий профилей
        vacancies_repo: Репозиторий вакансий
        courses_repo: Репозиторий курсов
        
    Returns:
        CareerDevelopmentResponse с курсами и вакансиями
        
    Raises:
        HTTPException: Если профиль не найден или произошла ошибка
    """
    try:
        return await service.get_career_development(
            request,
            profiles_repo,
            vacancies_repo,
            courses_repo,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get career development: {e}")

