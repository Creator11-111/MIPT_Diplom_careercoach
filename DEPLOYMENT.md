# Инструкция по развертыванию проекта

## Подготовка к загрузке в GitHub

### 1. Инициализация Git репозитория

```bash
cd financial_coach
git init
git add .
git commit -m "Initial commit: Financial Career Coach system"
```

### 2. Создание ветки для проекта

```bash
git branch -M main
# Или создайте отдельную ветку для диплома:
git checkout -b diploma-version
```

### 3. Подключение к удаленному репозиторию

```bash
git remote add origin https://github.com/Creator11-111/MIPT_Diplom_careercoach.git
```

### 4. Загрузка в GitHub

```bash
# Если репозиторий пустой:
git push -u origin main

# Или для отдельной ветки:
git push -u origin diploma-version
```

## Развертывание на Railway.app

### Шаг 1: Подготовка

1. Убедитесь, что код загружен в GitHub
2. Зайдите на https://railway.app
3. Войдите через GitHub

### Шаг 2: Создание проекта

1. Нажмите "New Project"
2. Выберите "Deploy from GitHub repo"
3. Выберите репозиторий `MIPT_Diplom_careercoach`
4. Railway автоматически определит Python и установит зависимости

### Шаг 3: Настройка переменных окружения

В настройках проекта (Settings → Variables) добавьте:

```
YANDEX_FOLDER_ID=ваш_folder_id
YANDEX_API_KEY=ваш_api_key
MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/dbname
MONGO_DB=financial_career_coach
APP_ENV=production
APP_HOST=0.0.0.0
```

### Шаг 4: Настройка MongoDB Atlas

1. Создайте бесплатный кластер на https://www.mongodb.com/cloud/atlas
2. Получите connection string
3. Добавьте IP Railway в whitelist (или 0.0.0.0/0 для теста)
4. Скопируйте `MONGO_URI` в Railway

### Шаг 5: Деплой

Railway автоматически задеплоит проект после подключения репозитория. После завершения вы получите URL вида: `https://your-project.up.railway.app`

## Развертывание на Render.com

### Шаг 1: Создание Web Service

1. Зайдите на https://render.com
2. New → Web Service
3. Подключите GitHub репозиторий

### Шаг 2: Настройка

- **Build Command**: `cd financial_coach && pip install -r requirements.txt`
- **Start Command**: `cd financial_coach && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Шаг 3: Переменные окружения

Добавьте те же переменные, что и для Railway

### Шаг 4: Деплой

Render автоматически задеплоит проект. URL будет вида: `https://your-service.onrender.com`

## Важные замечания

1. **FAISS индексы**: При первом запуске система построит индексы из эмбеддингов. Убедитесь, что файлы `data/embeddings/vacancies/*.npy` загружены в репозиторий или генерируются при старте.

2. **Размер данных**: Если эмбеддинги слишком большие для GitHub, рассмотрите:
   - Использование Git LFS
   - Генерацию эмбеддингов при старте приложения
   - Хранение в облачном хранилище (S3, Yandex Object Storage)

3. **Производительность**: На бесплатных тарифах возможны ограничения. Для продакшена рекомендуется платный тариф.

4. **Безопасность**: Никогда не коммитьте `.env` файлы с реальными ключами в Git!

