FROM python:3.12-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование структуры приложения поэтапно для лучшего кеширования
COPY app ./app
COPY static ./static
COPY data ./data
COPY configs ./configs

# Создаем необходимые директории если их нет
RUN mkdir -p static data/embeddings/vacancies data/embeddings/courses

# Проверяем что основные файлы на месте
RUN test -f app/main.py || (echo "ERROR: app/main.py not found!" && exit 1) && \
    test -f app/routers/sessions.py || (echo "ERROR: app/routers/sessions.py not found!" && exit 1) && \
    test -f static/index.html || (echo "ERROR: static/index.html not found!" && exit 1) && \
    grep -q "Anton Orlov" static/index.html && echo "Footer verified: Made by Anton Orlov" || echo "WARNING: Footer not found in index.html" && \
    echo "Files verified successfully"

# Переменная окружения для порта
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Открываем порт
EXPOSE 8080

# Запуск приложения через uvicorn напрямую
# Cloud Run sets PORT dynamically, so we use sh -c to expand it
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --timeout-keep-alive 60"]
