"""
Сервис для поиска подходящих вакансий для финансового специалиста

Использует двухэтапный поиск:
1. FAISS - семантический поиск по эмбеддингам
2. Stage 1 - фильтрация по названиям вакансий через LLM
3. Stage 2 - финальная фильтрация по описаниям через LLM
"""

from __future__ import annotations

import json
from typing import Any, List

from app.prompts import (
    MATCH_PREPROCESS_SYSTEM_PROMPT,
    MATCH_SYSTEM_PROMPT_STAGE1,
    MATCH_SYSTEM_PROMPT_STAGE2,
)
from app.services.yandex_sdk import embed_text, run_structured_completion, run_text_completion
from app.startup.load_embeddings import search_top_k
from app.models.match_models import (
    MatchVacanciesRequest,
    MatchVacanciesResponse,
    MatchedVacancy,
)
from app.repos.vacancy_repos import VacanciesRepository


class MatchService:
    """Сервис для поиска вакансий"""
    
    def preprocess_resume(self, resume: str) -> str:
        """
        Препроцессинг резюме для лучшего поиска
        
        Обогащает резюме ключевыми словами и финансовыми терминами
        для улучшения семантического поиска.
        
        Args:
            resume: Исходное резюме
            
        Returns:
            Обогащенное резюме
        """
        messages = [
            {"role": "system", "text": MATCH_PREPROCESS_SYSTEM_PROMPT},
            {"role": "user", "text": resume},
        ]
        # Используем простой text completion для препроцессинга
        from app.services.yandex_sdk import run_text_completion
        try:
            result = run_text_completion(messages).strip()
            return result if result else resume
        except RuntimeError as e:
            # Ошибка API ключа - пробрасываем дальше
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"YandexGPT API error in preprocess_resume: {e}")
            raise RuntimeError(f"YandexGPT API error: {str(e)}")
        except Exception:
            # Если препроцессинг не удался, возвращаем исходное резюме
            return resume

    def embed_query(self, text: str) -> Any:
        """
        Создает эмбеддинг для запроса
        
        Args:
            text: Текст запроса
            
        Returns:
            Эмбеддинг (numpy array)
            
        Raises:
            RuntimeError: Если произошла ошибка при создании эмбеддинга
        """
        try:
            return embed_text(text, model_kind="query")
        except RuntimeError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"YandexGPT Embeddings API error in embed_query: {e}")
            raise RuntimeError(f"YandexGPT Embeddings API error: {str(e)}")

    async def fetch_vacancies_in_order(
        self,
        repo: VacanciesRepository,
        top_idx: List[int]
    ) -> List[dict[str, Any]]:
        """
        Получает вакансии из базы в порядке индексов
        
        Args:
            repo: Репозиторий вакансий
            top_idx: Список idx вакансий в порядке релевантности
            
        Returns:
            Список вакансий в том же порядке
        """
        docs = await repo.find_by_ids(top_idx)
        by_idx = {int(d["idx"]): d for d in docs if "idx" in d}
        ordered = [by_idx.get(int(i)) for i in top_idx if int(i) in by_idx]
        return [d for d in ordered if d is not None]

    def stage1_select(
        self,
        system_prompt: str,
        context_text: str,
        limit: int
    ) -> List[int]:
        """
        Этап 1: Отбор вакансий по названиям
        
        Args:
            system_prompt: Промпт для LLM
            context_text: Контекст с резюме и списком вакансий
            limit: Максимальное количество вакансий
            
        Returns:
            Список idx отобранных вакансий
        """
        schema = {
            "title": "PickN",
            "type": "object",
            "properties": {
                "selected": {
                    "type": "array",
                    "items": {"type": "integer"}
                }
            },
            "required": ["selected"],
        }
        
        try:
            raw = run_structured_completion(
                [
                    {"role": "system", "text": system_prompt.format(limit=limit)},
                    {"role": "user", "text": context_text},
                ],
                schema,
                max_tokens=800
            )
            
            if not raw:
                return []
            
            data = json.loads(raw)
            selected = [int(x) for x in data.get("selected", []) if isinstance(x, int)]
        except RuntimeError as e:
            # Ошибка API ключа или доступа к YandexGPT
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"YandexGPT API error in stage1_select: {e}")
            raise RuntimeError(f"YandexGPT API error: {str(e)}")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in stage1_select: {e}")
            return []
        
        return selected[:limit]

    def stage2_select(
        self,
        system_prompt: str,
        detail_text: str,
        limit: int
    ) -> List[int]:
        """
        Этап 2: Финальный отбор по описаниям
        
        Args:
            system_prompt: Промпт для LLM
            detail_text: Контекст с резюме и подробными описаниями вакансий
            limit: Максимальное количество вакансий
            
        Returns:
            Список idx отобранных вакансий
        """
        return self.stage1_select(system_prompt, detail_text, limit)

    def mk_vacancy_block(self, vacancy: dict[str, Any]) -> str:
        """
        Форматирует вакансию в текстовый блок для LLM
        
        Args:
            vacancy: Словарь с данными вакансии
            
        Returns:
            Отформатированный текст
        """
        parts = []
        if vacancy.get("idx"):
            parts.append(f"idx: {vacancy['idx']}")
        if vacancy.get("title"):
            parts.append(f"Название: {vacancy['title']}")
        if vacancy.get("description"):
            parts.append(f"Описание: {vacancy['description']}")
        if vacancy.get("key_skills"):
            parts.append(f"Навыки: {vacancy['key_skills']}")
        if vacancy.get("company"):
            parts.append(f"Компания: {vacancy['company']}")
        if vacancy.get("location"):
            parts.append(f"Локация: {vacancy['location']}")
        if vacancy.get("salary"):
            parts.append(f"Зарплата: {vacancy['salary']}")
        if vacancy.get("experience"):
            parts.append(f"Опыт: {vacancy['experience']}")
        
        return "\n".join(parts)
    
    def determine_seniority_level(self, vacancy: dict[str, Any]) -> str:
        """
        Определяет уровень позиции (seniority) по названию, описанию и опыту
        
        Args:
            vacancy: Словарь с данными вакансии
            
        Returns:
            Уровень позиции: Стажер, Начальный, Средний, Продвинутый, Эксперт, Руководитель
        """
        title = (vacancy.get("title", "") or "").lower()
        description = (vacancy.get("description", "") or "").lower()
        experience = (vacancy.get("experience", "") or "").lower()
        key_skills = (vacancy.get("key_skills", "") or "").lower()
        
        text = f"{title} {description} {experience} {key_skills}"
        
        # Быстрая проверка по ключевым словам
        if any(word in text for word in ["стажер", "intern", "trainee", "без опыта", "обучение"]):
            return "Стажер"
        
        if any(word in text for word in ["руководитель", "директор", "head", "director", "chief", "cfo", "ceo", "cdo", "lead"]):
            return "Руководитель"
        
        if any(word in text for word in ["эксперт", "expert", "principal", "staff"]):
            return "Эксперт"
        
        if any(word in text for word in ["senior", "старший", "ведущий", "опыт от 3", "опыт от 5"]):
            return "Продвинутый"
        
        if any(word in text for word in ["middle", "средний", "опыт от 1", "опыт от 2"]):
            return "Средний"
        
        if any(word in text for word in ["junior", "младший", "начальный", "entry"]):
            return "Начальный"
        
        # Если ничего не найдено, используем LLM для определения
        try:
            prompt = f"""
Определи уровень позиции по следующей вакансии:

Название: {vacancy.get('title', '')}
Опыт: {vacancy.get('experience', '')}
Описание (первые 200 символов): {description[:200]}

Выбери ОДИН из уровней:
- Стажер (для позиций без опыта, с обучением)
- Начальный (junior, младший, для кандидатов с минимальным опытом до 1-2 лет)
- Средний (middle, для кандидатов с опытом 1-3 года)
- Продвинутый (senior, старший, для кандидатов с опытом 3+ лет)
- Эксперт (expert, principal, для высококвалифицированных специалистов)
- Руководитель (руководящие позиции: директор, руководитель, head, chief)

Верни ТОЛЬКО название уровня без дополнительных комментариев.
"""
            result = run_text_completion([{"role": "system", "text": prompt}]).strip()
            
            # Проверяем результат
            valid_levels = ["Стажер", "Начальный", "Средний", "Продвинутый", "Эксперт", "Руководитель"]
            for level in valid_levels:
                if level.lower() in result.lower():
                    return level
            
            return "Средний"  # По умолчанию
        except RuntimeError as e:
            # Ошибка API ключа или доступа к YandexGPT
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"YandexGPT API error in determine_seniority_level: {e}")
            # Возвращаем средний уровень по умолчанию, чтобы не ломать весь процесс
            return "Средний"
        except Exception as e:
            print(f"⚠️ Ошибка определения уровня позиции: {e}")
            return "Средний"  # По умолчанию

    async def match_vacancies(
        self,
        request: MatchVacanciesRequest,
        repo: VacanciesRepository,
    ) -> MatchVacanciesResponse:
        """
        Поиск подходящих вакансий для финансового специалиста
        
        Процесс:
        1. Препроцессинг резюме (обогащение ключевыми словами)
        2. Создание эмбеддинга запроса
        3. Поиск через FAISS (семантический поиск)
        4. Этап 1: Фильтрация по названиям через LLM
        5. Этап 2: Финальная фильтрация по описаниям через LLM
        
        Args:
            request: Запрос с резюме и параметрами поиска
            repo: Репозиторий вакансий
            
        Returns:
            MatchVacanciesResponse с найденными вакансиями
        """
        # 1. Препроцессинг и создание эмбеддинга
        aug_text = self.preprocess_resume(request.resume)
        q_vec = self.embed_query(aug_text)
        
        # 2. Поиск через FAISS (ОБЯЗАТЕЛЬНО должен работать)
        try:
            top_idx_list = search_top_k(q_vec, k=int(request.k_faiss))
            print(f"✅ FAISS нашел {len(top_idx_list)} кандидатов")
            
            if not top_idx_list or len(top_idx_list) == 0:
                error_msg = "FAISS вернул пустой список. Проверьте что индекс построен и эмбеддинги загружены."
                print(f"❌ {error_msg}")
                import logging
                logger = logging.getLogger(__name__)
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
        except RuntimeError as e:
            # FAISS должен всегда работать - если не работает, это критическая ошибка
            error_msg = f"❌ КРИТИЧЕСКАЯ ОШИБКА: FAISS поиск не работает: {e}"
            print(error_msg)
            print("💡 FAISS должен быть построен при запуске сервера!")
            print("💡 Проверьте:")
            print("   1. Построен ли FAISS индекс при запуске (см. логи запуска)")
            print("   2. Загружены ли эмбеддинги из /app/data/embeddings/vacancies")
            print("   3. Есть ли вакансии в MongoDB")
            print("   4. Проверьте логи запуска сервера на наличие ошибок FAISS")
            import logging
            logger = logging.getLogger(__name__)
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(f"FAISS search failed: {e}. FAISS must always work - check server startup logs.") from e
        except Exception as e:
            error_msg = f"❌ Неожиданная ошибка FAISS поиска: {e}"
            print(error_msg)
            import logging
            logger = logging.getLogger(__name__)
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(f"Unexpected FAISS error: {e}") from e
        
        # 3. Получаем вакансии из базы
        ordered = await self.fetch_vacancies_in_order(repo, top_idx_list)
        
        if not ordered or len(ordered) == 0:
            print(f"⚠️ Не найдено вакансий в базе для индексов: {top_idx_list[:10]}...")
            print(f"💡 Проверьте:")
            print(f"   1. Загружены ли вакансии в MongoDB (должно быть > 0)")
            print(f"   2. Соответствуют ли idx из FAISS индексам в MongoDB")
            print(f"   3. Проверьте логи seed_vacancies при запуске сервера")
            
            # Пытаемся получить хотя бы несколько вакансий напрямую из базы
            try:
                all_vacancies = await repo.find_all(limit=10)
                print(f"💡 В базе найдено {len(all_vacancies)} вакансий (проверка)")
                if len(all_vacancies) > 0:
                    print(f"   Пример idx из базы: {all_vacancies[0].get('idx', 'N/A')}")
            except Exception as e:
                print(f"   Ошибка проверки базы: {e}")
            
            return MatchVacanciesResponse(top_idx=top_idx_list, stage1=[], result=[])
        
        # 4. Этап 1: Фильтрация по названиям
        items = [f"{d['idx']}: {d.get('title', '')}" for d in ordered]
        list_text = "\n---\n".join(items)
        context1 = (
            f"Резюме финансового специалиста:\n{request.resume}\n\n"
            f"Список финансовых вакансий (id: название):\n{list_text}"
        )
        stage1_selected = set(
            self.stage1_select(
                MATCH_SYSTEM_PROMPT_STAGE1,
                context1,
                int(request.k_stage1)
            )
        )
        stage2 = [
            d for d in ordered
            if int(d["idx"]) in stage1_selected
        ][:int(request.k_stage1)] or ordered[:int(request.k_stage1)]

        # 5. Этап 2: Финальная фильтрация по описаниям
        details = "\n------\n".join(self.mk_vacancy_block(d) for d in stage2)
        context2 = (
            f"Резюме финансового специалиста:\n{request.resume}\n\n"
            f"Вакансии (подробно):\n{details}"
        )
        stage2_selected = set(
            self.stage2_select(
                MATCH_SYSTEM_PROMPT_STAGE2,
                context2,
                int(request.k_stage2)
            )
        )
        final = [
            d for d in stage2
            if int(d["idx"]) in stage2_selected
        ][:int(request.k_stage2)] or stage2[:int(request.k_stage2)]

        # 6. Преобразуем в MatchedVacancy с определением уровня
        result = []
        for d in final:
            seniority_level = self.determine_seniority_level(d)
            result.append(
                MatchedVacancy(
                    idx=int(d["idx"]),
                    title=d.get("title", ""),
                    company=d.get("company", ""),
                    location=d.get("location", ""),
                    salary=d.get("salary", ""),
                    experience=d.get("experience", ""),
                    job_type=d.get("job_type", ""),
                    description=d.get("description", ""),
                    key_skills=d.get("key_skills", ""),
                    hh_url=d.get("hh_url", "") or f"https://hh.ru/vacancy/{d.get('idx', '')}",
                    seniority_level=seniority_level,
                )
            )

        return MatchVacanciesResponse(
            top_idx=top_idx_list[:int(request.k_faiss)],
            stage1=list(stage1_selected),
            result=result
        )

