"""
Сервис для развития карьеры

Анализирует разрыв между текущей и желаемой позицией,
находит курсы для развития и вакансии на пути к цели.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from app.models.match_models import (
    CareerDevelopmentRequest,
    CareerDevelopmentResponse,
    MatchVacanciesRequest,
    MatchedCourse,
    MatchedVacancy,
)
from app.models import UserProfile
from app.repos.profile_repos import ProfilesRepository
from app.repos.vacancy_repos import VacanciesRepository
from app.repos.course_repos import CoursesRepository
from app.services.match_service import MatchService
from app.services.yandex_sdk import run_text_completion


def _build_search_url(provider: str, search_query: str) -> str:
    """Строит правильную поисковую ссылку для платформы"""
    provider_lower = provider.lower()
    encoded_query = quote(search_query)
    
    if 'coursera' in provider_lower:
        return f"https://www.coursera.org/search?query={encoded_query}"
    elif 'stepik' in provider_lower:
        return f"https://stepik.org/catalog/search?q={encoded_query}"
    elif 'нетология' in provider_lower or 'netology' in provider_lower:
        return f"https://netology.ru/search?q={encoded_query}"
    elif 'практикум' in provider_lower or 'practicum' in provider_lower:
        return f"https://practicum.yandex.ru/search/?q={encoded_query}"
    elif 'skillbox' in provider_lower:
        return f"https://skillbox.ru/search/?q={encoded_query}"
    elif 'geekbrains' in provider_lower or 'гикбрейнс' in provider_lower:
        return f"https://gb.ru/search?q={encoded_query}"
    else:
        # Если платформа неизвестна, используем общий поиск
        return f"https://www.google.com/search?q={encoded_query}+{quote(provider)}"


CAREER_GAP_ANALYSIS_PROMPT = """
Ты карьерный консультант для финансового сектора.
Проанализируй разрыв между текущей позицией пользователя и желаемой позицией.

Текущая позиция пользователя:
{current_profile}

Желаемая позиция: {target_position}
Целевая сфера: {target_field}
Целевая специализация: {target_specialization}

Задача:
1. Определи ключевые навыки и компетенции, которые нужны для желаемой позиции
2. Сравни с текущими навыками пользователя
3. Определи пробелы (gaps) - что нужно изучить/развить
4. Предложи конкретные навыки и области для обучения

Верни краткий анализ (2-3 абзаца) с конкретными рекомендациями по развитию.
"""


COURSE_SEARCH_PROMPT = """
Ты помогаешь финансовому специалисту найти курсы для развития карьеры.

Текущая позиция: {current_position}
Желаемая позиция: {target_position}
Пробелы в навыках: {gap_analysis}

Сформируй запрос для поиска курсов, который включает:
- Название желаемой позиции
- Конкретные навыки, которые нужно развить
- Финансовые инструменты и системы
- Профессиональные сертификаты (если нужны)

Верни только текст запроса для поиска курсов (без комментариев).
"""


FUTURE_VACANCIES_PROMPT = """
Ты помогаешь финансовому специалисту найти вакансии на пути к желаемой позиции.

Текущая позиция: {current_position}
Желаемая позиция: {target_position}
Пройденные курсы/навыки: {acquired_skills}

Сформируй описание "будущего резюме" после прохождения курсов:
- Укажи промежуточные позиции на пути к цели
- Добавь навыки, полученные на курсах
- Укажи уровень (junior/middle/senior/lead)
- Добавь финансовые инструменты и компетенции

Верни только текст резюме для поиска вакансий (без комментариев).
"""


class CareerDevelopmentService:
    """Сервис для развития карьеры"""
    
    def __init__(self) -> None:
        self.match_service = MatchService()
    
    def _build_resume_from_profile(self, profile: UserProfile) -> str:
        """Строит текст резюме из профиля"""
        resume_parts = []
        
        if profile.professional_context:
            if profile.professional_context.professional_role:
                resume_parts.append(f"Текущая позиция: {profile.professional_context.professional_role}")
            if profile.professional_context.professional_field:
                resume_parts.append(f"Сфера: {profile.professional_context.professional_field}")
            if profile.professional_context.specialization:
                resume_parts.append(f"Специализация: {profile.professional_context.specialization}")
            if profile.professional_context.seniority_level:
                resume_parts.append(f"Уровень: {profile.professional_context.seniority_level}")
        
        if profile.resume:
            resume_parts.append("\nОпыт работы:")
            for item in profile.resume:
                job_desc = []
                if item.title:
                    job_desc.append(item.title)
                if item.company:
                    job_desc.append(f"в {item.company}")
                if job_desc:
                    resume_parts.append(f"- {' '.join(job_desc)}")
                if item.tasks:
                    resume_parts.append(f"  Задачи: {', '.join(item.tasks[:3])}")
                if item.tech_stack:
                    resume_parts.append(f"  Инструменты: {', '.join(item.tech_stack)}")
        
        if profile.skills:
            if profile.skills.hard_skills:
                resume_parts.append(f"\nНавыки: {', '.join(profile.skills.hard_skills)}")
            if profile.skills.tools:
                resume_parts.append(f"Инструменты: {', '.join(profile.skills.tools)}")
        
        return "\n".join(resume_parts)
    
    async def analyze_career_gap(
        self,
        profile: UserProfile,
        target_position: str,
        target_field: str | None,
        target_specialization: str | None,
    ) -> str:
        """Анализирует разрыв между текущей и желаемой позицией"""
        current_profile_text = self._build_resume_from_profile(profile)
        
        messages = [
            {
                "role": "system",
                "text": CAREER_GAP_ANALYSIS_PROMPT.format(
                    current_profile=current_profile_text,
                    target_position=target_position,
                    target_field=target_field or "та же сфера",
                    target_specialization=target_specialization or "та же специализация",
                )
            }
        ]
        
        try:
            gap_analysis = run_text_completion(messages).strip()
            return gap_analysis
        except Exception as e:
            print(f"⚠️ Ошибка анализа разрыва: {e}")
            return f"Для перехода на позицию {target_position} необходимо развить навыки в области финансового управления, стратегического планирования и лидерства."
    
    async def find_development_courses(
        self,
        current_position: str,
        target_position: str,
        gap_analysis: str,
        courses_repo: CoursesRepository,
    ) -> list[MatchedCourse]:
        """Находит курсы для развития к желаемой позиции"""
        # Формируем запрос для поиска курсов
        messages = [
            {
                "role": "system",
                "text": COURSE_SEARCH_PROMPT.format(
                    current_position=current_position,
                    target_position=target_position,
                    gap_analysis=gap_analysis,
                )
            }
        ]
        
        try:
            course_query = run_text_completion(messages).strip()
        except Exception:
            course_query = f"{target_position} финансовый менеджмент стратегическое планирование"
        
        # Пока используем упрощенный подход - генерируем рекомендации через LLM
        # В будущем можно добавить FAISS индекс для курсов и реальную базу
        
        # Генерируем список курсов через LLM на основе gap_analysis
        course_recommendations_prompt = f"""
На основе анализа разрыва между текущей позицией "{current_position}" и желаемой "{target_position}",
предложи 5-7 конкретных курсов для развития.

Анализ разрыва:
{gap_analysis}

ВАЖНО: Для каждого курса укажи:
1. Название курса (реальное название, как оно может быть на платформе)
2. Провайдер (Coursera, Stepik, Нетология, Яндекс.Практикум, Skillbox, или другая платформа)
3. Навыки, которые дает курс
4. Уровень (начальный/средний/продвинутый)
5. Язык курса (Русский, English, или другой)
6. Поисковый запрос - короткий запрос для поиска этого курса на платформе (2-5 ключевых слов)

НЕ придумывай ссылки вида /номер-курса или /название-курса! Это не работает.
Вместо этого укажи реальный поисковый запрос, который можно использовать для поиска курса на платформе.

Верни список курсов в формате:
1. Название | Провайдер | Навыки | Уровень | Язык | Поисковый запрос
2. ...

Пример:
1. Финансовый менеджмент и стратегия | Coursera | Финансовое планирование, бюджетирование, стратегический анализ | Средний | Русский | financial management strategy
2. Excel для финансовых аналитиков | Нетология | Excel, финансовое моделирование, анализ данных | Начальный | Русский | excel финансовый анализ
"""
        
        try:
            courses_text = run_text_completion([{"role": "system", "text": course_recommendations_prompt}]).strip()
            
            # Парсим ответ и создаем MatchedCourse объекты
            courses = []
            lines = courses_text.split('\n')
            idx = 1
            
            for line in lines:
                line = line.strip()
                if not line or not line[0].isdigit():
                    continue
                
                # Парсим строку вида "1. Название | Провайдер | Навыки | Уровень | Язык | Поисковый запрос"
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    name = parts[0].split('.', 1)[-1].strip() if '.' in parts[0] else parts[0]
                    provider = parts[1] if len(parts) > 1 else ""
                    skills = parts[2] if len(parts) > 2 else ""
                    level = parts[3] if len(parts) > 3 else ""
                    language = parts[4] if len(parts) > 4 else "Русский"
                    search_query = parts[5] if len(parts) > 5 else name
                    
                    # Строим правильную поисковую ссылку
                    url = _build_search_url(provider, search_query) if provider and search_query else ""
                    
                    # Проверяем валидность URL перед добавлением
                    if url and url.startswith(('http://', 'https://')):
                        try:
                            # Дополнительная проверка URL
                            from urllib.parse import urlparse
                            parsed = urlparse(url)
                            if parsed.netloc:  # URL должен иметь домен
                                courses.append(MatchedCourse(
                                    idx=idx,
                                    name=name,
                                    provider=provider,
                                    url=url,
                                    description=f"Курс для развития навыков: {skills}",
                                    skills=skills,
                                    level=level,
                                    duration="",
                                    language=language,
                                ))
                                idx += 1
                        except Exception:
                            # Если URL невалидный, пропускаем курс
                            continue
                    
                    if idx > 10:  # Ограничиваем до 10 курсов
                        break
            
            # Возвращаем только курсы с валидными URL
            return courses[:10]
            
        except Exception as e:
            print(f"⚠️ Ошибка генерации курсов: {e}")
            # Возвращаем базовые рекомендации с правильными поисковыми ссылками
            return [
                MatchedCourse(
                    idx=1,
                    name=f"Финансовый менеджмент для {target_position}",
                    provider="Coursera",
                    url=f"https://www.coursera.org/search?query={quote('financial management strategy')}",
                    description=f"Курс для развития навыков финансового менеджмента на пути к позиции {target_position}.",
                    skills="Финансовый менеджмент, стратегическое планирование, бюджетирование",
                    level="Средний",
                    duration="",
                    language="Русский / English",
                ),
                MatchedCourse(
                    idx=2,
                    name=f"Лидерство и управление командой",
                    provider="Нетология",
                    url=f"https://netology.ru/search?q={quote('лидерство управление командой')}",
                    description=f"Курс для развития лидерских навыков, необходимых для позиции {target_position}.",
                    skills="Лидерство, управление командой, коммуникации",
                    level="Средний",
                    duration="",
                    language="Русский",
                ),
            ]
    
    async def find_future_vacancies(
        self,
        current_position: str,
        target_position: str,
        acquired_skills: str,
        vacancies_repo: VacanciesRepository,
    ) -> list[MatchedVacancy]:
        """Находит вакансии на пути к желаемой позиции (после прохождения курсов)"""
        # Формируем "будущее резюме" с новыми навыками
        messages = [
            {
                "role": "system",
                "text": FUTURE_VACANCIES_PROMPT.format(
                    current_position=current_position,
                    target_position=target_position,
                    acquired_skills=acquired_skills,
                )
            }
        ]
        
        try:
            future_resume = run_text_completion(messages).strip()
        except Exception:
            future_resume = f"Финансовый специалист с опытом в {current_position}, развивающийся в направлении {target_position}. Навыки: {acquired_skills}"
        
        # Ищем вакансии через MatchService
        request = MatchVacanciesRequest(
            resume=future_resume,
            k_faiss=100,
            k_stage1=30,
            k_stage2=15,
        )
        
        try:
            response = await self.match_service.match_vacancies(request, vacancies_repo)
            return response.result
        except Exception as e:
            print(f"⚠️ Ошибка поиска вакансий развития: {e}")
            return []
    
    async def get_career_development(
        self,
        request: CareerDevelopmentRequest,
        profiles_repo: ProfilesRepository,
        vacancies_repo: VacanciesRepository,
        courses_repo: CoursesRepository,
    ) -> CareerDevelopmentResponse:
        """
        Получить план развития карьеры: курсы и вакансии для перехода к желаемой позиции
        
        Args:
            request: Запрос с session_id и целевой позицией
            profiles_repo: Репозиторий профилей
            vacancies_repo: Репозиторий вакансий
            courses_repo: Репозиторий курсов
            
        Returns:
            CareerDevelopmentResponse с курсами и вакансиями
        """
        # Получаем профиль пользователя
        profile_doc = await profiles_repo.find_by_session_id(request.session_id)
        if not profile_doc:
            raise ValueError("Profile not found. Please complete the interview and build profile first.")
        
        profile = UserProfile.model_validate(profile_doc.get("profile", {}))
        
        # Определяем текущую позицию
        current_position = (
            profile.professional_context.professional_role 
            if profile.professional_context and profile.professional_context.professional_role
            else "Финансовый специалист"
        )
        
        # Анализируем разрыв
        gap_analysis = await self.analyze_career_gap(
            profile,
            request.target_position,
            request.target_field,
            request.target_specialization,
        )
        
        # Находим курсы для развития
        courses = await self.find_development_courses(
            current_position,
            request.target_position,
            gap_analysis,
            courses_repo,
        )
        
        # Формируем список полученных навыков из курсов
        acquired_skills = ", ".join([c.skills or c.name or "" for c in courses[:5] if c.skills or c.name])
        if not acquired_skills:
            # Если курсов нет, используем базовые навыки из gap_analysis
            acquired_skills = gap_analysis[:200] if gap_analysis else f"Навыки для позиции {request.target_position}"
        
        # Находим вакансии на пути к цели
        future_vacancies = await self.find_future_vacancies(
            current_position,
            request.target_position,
            acquired_skills,
            vacancies_repo,
        )
        
        return CareerDevelopmentResponse(
            current_position=current_position,
            target_position=request.target_position,
            gap_analysis=gap_analysis,
            courses=courses,
            future_vacancies=future_vacancies,
        )

