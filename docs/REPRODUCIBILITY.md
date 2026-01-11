# Воспроизводимость результатов

**Дата:** 2025-01-12  
**Версия:** 1.0.0

---

## 1. Требования к окружению

### 1.1 Программное обеспечение

- **Python:** 3.12+
- **MongoDB:** 6.0+ (рекомендуется MongoDB Atlas)
- **Docker:** 24.0+ (для контейнеризации)

### 1.2 Зависимости Python

Все зависимости зафиксированы в `requirements.txt`:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
motor==3.3.2
pydantic==2.5.2
faiss-cpu==1.7.4
numpy==1.26.2
polars==0.19.19
yandexcloud==0.295.0
grpcio==1.60.0
```

### 1.3 API ключи

- **YandexGPT:** YANDEX_FOLDER_ID, YANDEX_API_KEY
- **MongoDB Atlas:** MONGO_URI

---

## 2. Данные

### 2.1 Вакансии

**Источник:** HeadHunter.ru (офлайн-снимок)  
**Формат:** Apache Parquet  
**Путь:** `data/financial_vacancies.parquet`  
**Количество:** ~2574 вакансии финансового сектора

**Поля:**
- idx: уникальный идентификатор
- title: название вакансии
- company: компания
- description: описание
- key_skills: навыки
- salary: зарплата
- location: локация
- experience: требуемый опыт

### 2.2 Эмбеддинги

**Путь:** `data/embeddings/vacancies/`  
**Формат:** NumPy arrays (.npy)  
**Размерность:** 256  
**Количество батчей:** 1287

Файлы:
- `embeddings_batch_N.npy` — векторы эмбеддингов
- `indices_batch_N.npy` — соответствующие idx вакансий

---

## 3. Воспроизведение экспериментов

### 3.1 Локальный запуск

```bash
# 1. Клонирование
git clone <repository>
cd financial_coach

# 2. Установка зависимостей
pip install -r requirements.txt

# 3. Настройка переменных окружения
cp configs/example.env .env
# Отредактировать .env с реальными ключами

# 4. Запуск
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### 3.2 Docker

```bash
# Сборка образа
docker build -t financial-coach .

# Запуск
docker run -p 8080:8080 \
  -e MONGO_URI="..." \
  -e YANDEX_FOLDER_ID="..." \
  -e YANDEX_API_KEY="..." \
  financial-coach
```

### 3.3 Google Cloud Run

```bash
# Деплой через скрипт
./DEPLOY_NOW.bat

# Или вручную
gcloud run deploy financial-career-coach \
  --source . \
  --platform managed \
  --region us-central1 \
  --memory 4Gi \
  --cpu 2
```

---

## 4. Генерация эмбеддингов

Для воспроизведения эмбеддингов с нуля:

```bash
# 1. Убедиться что есть данные
ls data/financial_vacancies.parquet

# 2. Настроить API ключи
export YANDEX_FOLDER_ID="..."
export YANDEX_API_KEY="..."

# 3. Запустить генерацию
python data_parsing/generate_embeddings.py
```

**Время:** ~2-3 часа для 2574 вакансий  
**Ограничения API:** ~10 запросов/сек

---

## 5. Тестирование

### 5.1 Unit-тесты

```bash
pytest tests/ -v
```

### 5.2 Проверка синтаксиса

```bash
python -m py_compile app/main.py
python -m py_compile app/routers/sessions.py
python -m compileall app/
```

### 5.3 Health check

```bash
curl http://localhost:8080/health
# {"status": "ok", "time": "..."}

curl http://localhost:8080/ready
# {"ready": true, "faiss_built": true, "vacancies_count": 2574}
```

---

## 6. Структура репозитория

```
financial_coach/
├── app/                    # Исходный код приложения
│   ├── main.py            # Точка входа
│   ├── routers/           # API endpoints
│   ├── services/          # Бизнес-логика
│   ├── repos/             # Репозитории БД
│   └── startup/           # Инициализация
├── data/                   # Данные
│   ├── embeddings/        # Эмбеддинги
│   └── financial_vacancies.parquet
├── data_parsing/           # Скрипты парсинга
├── docs/                   # Документация
├── Thesis/                 # Материалы диплома
├── tests/                  # Тесты
├── Dockerfile             # Контейнеризация
└── requirements.txt       # Зависимости
```

---

## 7. Известные ограничения

1. **Эмбеддинги зависят от версии YandexGPT** — при смене модели нужна перегенерация
2. **FAISS индекс в памяти** — требует ~1GB RAM для 2574 вакансий
3. **Холодный старт** — первый запуск занимает 30-60 сек (загрузка FAISS)

---

**Document Status:** ✅ Complete
