# Деплой Méridien Career Coach

## Вариант 1: Railway (Рекомендуется - бесплатно)

### Шаг 1: Создать аккаунт
1. Зайди на https://railway.app/
2. Войди через GitHub

### Шаг 2: Создать проект
1. Нажми **New Project** → **Deploy from GitHub repo**
2. Выбери свой репозиторий `financial_coach`
3. Railway автоматически обнаружит Dockerfile

### Шаг 3: Добавить переменные окружения
В настройках проекта (Variables) добавь:

```
APP_ENV=production
MONGO_URI=mongodb+srv://YOUR_USER:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/financial_career_coach
MONGO_DB=financial_career_coach
YANDEX_FOLDER_ID=your_folder_id
YANDEX_API_KEY=your_api_key
CORS_ORIGINS=*
```

> **Примечание**: Возьми реальные значения из файла `.env` в корне проекта.

### Шаг 4: Деплой
Railway автоматически задеплоит. Получишь URL типа:
`https://financial-coach-production.up.railway.app`

---

## Вариант 2: Render (Бесплатно)

1. Зайди на https://render.com/
2. New → Web Service → Connect GitHub
3. Environment: Docker
4. Добавь переменные окружения (как выше)

---

## Вариант 3: Google Cloud Run

```bash
# Установи gcloud CLI, затем:
gcloud run deploy financial-career-coach \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars="APP_ENV=production,MONGO_URI=...,YANDEX_FOLDER_ID=...,YANDEX_API_KEY=..."
```

---

## Быстрый деплой через GitHub

Если проект уже на GitHub, просто:

1. Запушь изменения:
```bash
git add .
git commit -m "Add new Méridien design"
git push
```

2. Подключи Railway/Render к репозиторию — деплой автоматический при каждом push.
