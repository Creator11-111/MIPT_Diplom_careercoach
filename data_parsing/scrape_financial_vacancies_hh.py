"""
Скрипт для парсинга финансовых вакансий с сайта HH.ru

Этот скрипт собирает вакансии из финансового и банковского сектора
и сохраняет их в формат Parquet для дальнейшей обработки.

ВАЖНО: HH.ru имеет API для работы с вакансиями. 
Мы используем официальный API, который требует регистрации приложения.
"""

from __future__ import annotations

import os
import time
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
import polars as pl
from tqdm import tqdm


# Финансовые категории для поиска на HH.ru
FINANCIAL_CATEGORIES = [
    "Финансовый аналитик",
    "Финансовый директор",
    "Финансовый менеджер",
    "Банковский специалист",
    "Кредитный специалист",
    "Инвестиционный менеджер",
    "Аудитор",
    "Бухгалтер",
    "Риск-менеджер",
    "Казначей",
    "Специалист по МСФО",
    "Финансовый контролер",
    "Специалист по финансовому планированию",
    "Аналитик по кредитным рискам",
]


class HHVacancyScraper:
    """
    Класс для парсинга вакансий с HH.ru через официальный API
    
    Как это работает:
    1. Используем официальный API HH.ru (не парсинг HTML)
    2. Ищем вакансии по финансовым категориям
    3. Сохраняем данные в структурированном виде
    """
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Инициализация скрапера
        
        Args:
            api_token: API токен от HH.ru (если есть)
                      Если нет - можно использовать без авторизации для публичных данных
        """
        self.api_token = api_token
        self.base_url = "https://api.hh.ru"
        self.headers = {
            "User-Agent": "FinancialCareerCoach/1.0 (financial-coach-bot@example.com)"
        }
        if api_token:
            self.headers["Authorization"] = f"Bearer {api_token}"
        
        # Задержка между запросами (чтобы не перегружать API)
        self.delay_seconds = 0.2
        
    def search_vacancies(
        self, 
        text: str, 
        area: int = 1,  # 1 = Москва, 2 = Санкт-Петербург, 113 = Россия
        per_page: int = 100,
        max_pages: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Поиск вакансий по тексту запроса
        
        Args:
            text: Текст для поиска (например, "Финансовый аналитик")
            area: ID региона (1=Москва, 2=СПб, 113=Россия)
            per_page: Количество вакансий на странице (макс 100)
            max_pages: Максимальное количество страниц для обработки
            
        Returns:
            Список словарей с данными о вакансиях
        """
        vacancies = []
        page = 0
        
        print(f"🔍 Ищем вакансии по запросу: '{text}'...")
        
        while page < max_pages:
            try:
                # Параметры запроса к API
                params = {
                    "text": text,
                    "area": area,
                    "per_page": per_page,
                    "page": page,
                    "only_with_salary": False,  # Включаем вакансии с зарплатой и без
                }
                
                # Отправляем запрос к API
                response = requests.get(
                    f"{self.base_url}/vacancies",
                    params=params,
                    headers=self.headers,
                    timeout=10
                )
                
                # Проверяем успешность запроса
                if response.status_code != 200:
                    print(f"⚠️  Ошибка запроса: {response.status_code}")
                    break
                
                data = response.json()
                
                # Если вакансий нет - прекращаем
                if not data.get("items"):
                    break
                
                # Получаем детальную информацию о каждой вакансии
                for item in tqdm(data["items"], desc=f"Страница {page + 1}"):
                    vacancy_detail = self.get_vacancy_details(item["id"])
                    if vacancy_detail:
                        vacancies.append(vacancy_detail)
                    
                    # Небольшая задержка между запросами
                    time.sleep(self.delay_seconds)
                
                # Проверяем, есть ли еще страницы
                pages = data.get("pages", 0)
                found = data.get("found", 0)
                
                print(f"📊 Найдено: {found} вакансий, страниц: {pages}, обработано: {len(vacancies)}")
                
                if page >= pages - 1:
                    break
                
                page += 1
                time.sleep(self.delay_seconds)
                
            except Exception as e:
                print(f"❌ Ошибка при обработке страницы {page}: {e}")
                break
        
        return vacancies
    
    def get_vacancy_details(self, vacancy_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение детальной информации о вакансии
        
        Args:
            vacancy_id: ID вакансии на HH.ru
            
        Returns:
            Словарь с данными о вакансии или None при ошибке
        """
        try:
            response = requests.get(
                f"{self.base_url}/vacancies/{vacancy_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            # Извлекаем нужные поля
            salary = data.get("salary")
            salary_str = ""
            if salary:
                if salary.get("from") and salary.get("to"):
                    salary_str = f"{salary['from']} - {salary['to']} {salary.get('currency', 'RUR')}"
                elif salary.get("from"):
                    salary_str = f"от {salary['from']} {salary.get('currency', 'RUR')}"
                elif salary.get("to"):
                    salary_str = f"до {salary['to']} {salary.get('currency', 'RUR')}"
            
            # Опыт работы
            experience = data.get("experience", {})
            experience_str = experience.get("name", "") if experience else ""
            
            # Навыки
            skills = [skill.get("name", "") for skill in data.get("key_skills", [])]
            skills_str = ", ".join(skills) if skills else ""
            
            # Описание (убираем HTML теги)
            description = data.get("description", "")
            # Простая очистка HTML (можно использовать beautifulsoup4 для более точной)
            description = description.replace("<p>", "").replace("</p>", "\n")
            description = description.replace("<br>", "\n").replace("<br/>", "\n")
            description = description.replace("<li>", "- ").replace("</li>", "\n")
            description = description.replace("<ul>", "").replace("</ul>", "")
            description = description.replace("<strong>", "").replace("</strong>", "")
            description = description.replace("<em>", "").replace("</em>", "")
            # Убираем множественные пробелы и переносы
            description = " ".join(description.split())
            
            # Компания
            employer = data.get("employer", {})
            company = employer.get("name", "") if employer else ""
            
            # Локация
            area_data = data.get("area", {})
            location = area_data.get("name", "") if area_data else ""
            
            # Тип работы
            employment = data.get("employment", {})
            job_type = employment.get("name", "") if employment else ""
            
            # Дата публикации
            published_at = data.get("published_at", "")
            
            return {
                "idx": int(vacancy_id),  # Используем ID вакансии как индекс
                "№": int(vacancy_id),
                "id": int(vacancy_id),
                "title": data.get("name", ""),
                "salary": salary_str,
                "experience": experience_str,
                "job_type": job_type,
                "description": description[:5000] if len(description) > 5000 else description,  # Ограничиваем длину
                "key_skills": skills_str,
                "company": company,
                "location": location,
                "date_of_post": published_at,
                "type": "financial",  # Маркер для финансовых вакансий
                "hh_url": data.get("alternate_url", ""),
            }
            
        except Exception as e:
            print(f"⚠️  Ошибка при получении деталей вакансии {vacancy_id}: {e}")
            return None
    
    def scrape_all_financial_vacancies(
        self, 
        area: int = 113,  # По умолчанию ищем по всей России
        max_per_category: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Сбор всех финансовых вакансий по категориям
        
        Args:
            area: ID региона (113 = Россия)
            max_per_category: Максимум вакансий на категорию
            
        Returns:
            Список всех найденных вакансий
        """
        all_vacancies = []
        seen_ids = set()  # Для удаления дубликатов
        
        print("🚀 Начинаем сбор финансовых вакансий...")
        print(f"📋 Категорий для поиска: {len(FINANCIAL_CATEGORIES)}")
        
        for category in FINANCIAL_CATEGORIES:
            print(f"\n{'='*60}")
            print(f"📂 Категория: {category}")
            print(f"{'='*60}")
            
            vacancies = self.search_vacancies(
                text=category,
                area=area,
                per_page=100,
                max_pages=max_per_category // 100
            )
            
            # Удаляем дубликаты
            for vacancy in vacancies:
                vacancy_id = vacancy.get("id")
                if vacancy_id and vacancy_id not in seen_ids:
                    seen_ids.add(vacancy_id)
                    all_vacancies.append(vacancy)
            
            print(f"✅ Собрано уникальных вакансий из категории '{category}': {len(vacancies)}")
            print(f"📊 Всего собрано: {len(all_vacancies)}")
            
            # Пауза между категориями
            time.sleep(1)
        
        print(f"\n🎉 Итого собрано уникальных вакансий: {len(all_vacancies)}")
        return all_vacancies
    
    def save_to_parquet(self, vacancies: List[Dict[str, Any]], output_path: str):
        """
        Сохранение вакансий в Parquet формат
        
        Args:
            vacancies: Список словарей с вакансиями
            output_path: Путь для сохранения файла
        """
        if not vacancies:
            print("⚠️  Нет данных для сохранения")
            return
        
        print(f"\n💾 Сохраняем {len(vacancies)} вакансий в {output_path}...")
        
        # Создаем DataFrame из данных
        df = pl.DataFrame(vacancies)
        
        # Сохраняем в Parquet
        df.write_parquet(output_path, compression="snappy")
        
        print(f"✅ Данные сохранены в {output_path}")
        print(f"📊 Размер файла: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")


def main():
    """
    Главная функция для запуска скрипта
    """
    print("="*60)
    print("🏦 ПАРСИНГ ФИНАНСОВЫХ ВАКАНСИЙ С HH.RU")
    print("="*60)
    print()
    
    # Создаем директорию для данных, если её нет
    os.makedirs("financial_coach/data", exist_ok=True)
    
    # Инициализируем скрапер
    # Примечание: Для работы без ограничений можно получить API токен на https://hh.ru/oauth/applications
    scraper = HHVacancyScraper(api_token=None)  # Можно указать токен, если есть
    
    # Собираем вакансии
    # По умолчанию ищем по всей России (area=113)
    # Можно изменить на 1 (Москва) или 2 (СПб)
    vacancies = scraper.scrape_all_financial_vacancies(
        area=113,  # 113 = Россия, 1 = Москва, 2 = СПб
        max_per_category=500  # Максимум 500 вакансий на категорию
    )
    
    # Сохраняем в Parquet
    output_path = "financial_coach/data/financial_vacancies.parquet"
    scraper.save_to_parquet(vacancies, output_path)
    
    print("\n" + "="*60)
    print("✅ ГОТОВО! Вакансии сохранены.")
    print("="*60)
    print(f"\n📝 Следующий шаг: запустите скрипт для генерации эмбеддингов")
    print(f"   python financial_coach/data_parsing/generate_embeddings.py")


if __name__ == "__main__":
    main()














