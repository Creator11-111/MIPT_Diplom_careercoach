# Deployment Documentation

**Date:** 2025-01-12  
**Version:** 1.0.0

---

## 1. Overview

Документ описывает процесс развертывания системы Financial Career Coach на Google Cloud Run.

---

## 2. Prerequisites

### 2.1 Required Accounts

- **Google Cloud Platform:** Аккаунт с доступом к Cloud Run
- **MongoDB Atlas:** Аккаунт для базы данных
- **Yandex Cloud:** Аккаунт с доступом к YandexGPT API

### 2.2 Required Tools

- `gcloud` CLI (Google Cloud SDK)
- `docker` (для локальной сборки, опционально)
- Python 3.12+ (для локальной разработки)

### 2.3 Required Resources

- **MongoDB Atlas:** Free tier или выше
- **YandexGPT API:** Доступ к API (платный)
- **Google Cloud Run:** Доступ к сервису

---

## 3. Environment Setup

### 3.1 Google Cloud Setup

**1. Install gcloud CLI:**
```bash
# Download from https://cloud.google.com/sdk/docs/install
# Or use package manager
```

**2. Authenticate:**
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

**3. Enable APIs:**
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 3.2 MongoDB Atlas Setup

**1. Create Cluster:**
- Зайти на https://www.mongodb.com/cloud/atlas
- Создать бесплатный кластер (M0)
- Выбрать регион (рекомендуется: близко к Cloud Run)

**2. Create Database User:**
- Database Access → Add New Database User
- Username и password
- Role: `Atlas Admin` (или ограниченные права)

**3. Whitelist IP:**
- Network Access → Add IP Address
- Для Cloud Run: `0.0.0.0/0` (все IP) или конкретные IP

**4. Get Connection String:**
- Clusters → Connect → Connect your application
- Скопировать connection string
- Заменить `<password>` на пароль пользователя

### 3.3 Yandex Cloud Setup

**1. Create Folder:**
- Зайти на https://console.cloud.yandex.ru
- Создать папку (folder)

**2. Get API Key:**
- IAM → Service Accounts → Create
- Создать сервисный аккаунт
- Выдать права на использование YandexGPT
- Создать API ключ

**3. Get Folder ID:**
- Скопировать ID папки из URL или настроек

---

## 4. Configuration

### 4.1 Environment Variables

Создайте файл `.env` (не коммитьте в репозиторий):

```bash
# Application
APP_ENV=production
HOST=0.0.0.0
PORT=8080

# MongoDB
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/financial_coach?retryWrites=true&w=majority

# YandexGPT
YANDEX_FOLDER_ID=your-folder-id
YANDEX_API_KEY=your-api-key
# OR use IAM token instead:
# YANDEX_IAM_TOKEN=your-iam-token

# CORS (production: specify domains)
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### 4.2 Google Cloud Secrets (Recommended)

**1. Create Secrets:**
```bash
echo -n "your-mongo-uri" | gcloud secrets create mongo-uri --data-file=-
echo -n "your-api-key" | gcloud secrets create yandex-api-key --data-file=-
echo -n "your-folder-id" | gcloud secrets create yandex-folder-id --data-file=-
```

**2. Grant Access:**
```bash
gcloud secrets add-iam-policy-binding mongo-uri \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## 5. Docker Build

### 5.1 Local Build (Testing)

**1. Build Image:**
```bash
cd financial_coach
docker build -t financial-career-coach:latest .
```

**2. Test Locally:**
```bash
docker run -p 8080:8080 \
  -e MONGO_URI="your-mongo-uri" \
  -e YANDEX_API_KEY="your-api-key" \
  -e YANDEX_FOLDER_ID="your-folder-id" \
  financial-career-coach:latest
```

**3. Test Health:**
```bash
curl http://localhost:8080/health
curl http://localhost:8080/ready
```

### 5.2 Cloud Build

**1. Submit Build:**
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/financial-career-coach
```

**2. Or Use Cloud Build Config:**
```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/financial-career-coach', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/financial-career-coach']
```

---

## 6. Deployment to Cloud Run

### 6.1 First Deployment

**1. Deploy Service:**
```bash
gcloud run deploy financial-career-coach \
  --image gcr.io/YOUR_PROJECT_ID/financial-career-coach \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 600 \
  --max-instances 10 \
  --set-env-vars "APP_ENV=production,HOST=0.0.0.0,PORT=8080" \
  --set-secrets "MONGO_URI=mongo-uri:latest,YANDEX_API_KEY=yandex-api-key:latest,YANDEX_FOLDER_ID=yandex-folder-id:latest"
```

**2. Or Use Deploy Script:**
```bash
# Use DEPLOY_NOW.bat (Windows) or create deploy.sh (Linux/Mac)
./DEPLOY_NOW.bat
```

### 6.2 Update Deployment

**1. Rebuild and Deploy:**
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/financial-career-coach
gcloud run deploy financial-career-coach \
  --image gcr.io/YOUR_PROJECT_ID/financial-career-coach \
  --platform managed \
  --region us-central1
```

**2. Or Use CI/CD:**
- Настроить Cloud Build triggers
- Автоматический деплой при push в main branch

---

## 7. Post-Deployment

### 7.1 Verify Deployment

**1. Check Health:**
```bash
curl https://your-service-url.run.app/health
curl https://your-service-url.run.app/ready
```

**2. Check Logs:**
```bash
gcloud run services logs read financial-career-coach \
  --region us-central1 \
  --limit 50
```

**3. Test API:**
```bash
# Create session
curl -X POST https://your-service-url.run.app/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user"}'
```

### 7.2 Monitor

**1. Cloud Run Metrics:**
- Requests per second
- Latency (p50, p95, p99)
- Error rate
- Memory/CPU usage

**2. Application Logs:**
- Structured logging через Cloud Logging
- Алерты на критические ошибки

**3. External Services:**
- MongoDB Atlas monitoring
- YandexGPT API usage

---

## 8. Scaling Configuration

### 8.1 Current Settings

- **Memory:** 4Gi
- **CPU:** 2 cores
- **Max Instances:** 10
- **Min Instances:** 0 (scale to zero)
- **Timeout:** 600 seconds

### 8.2 Scaling Recommendations

**For Production:**
- **Min Instances:** 1 (для быстрого старта)
- **Max Instances:** 20-50 (в зависимости от нагрузки)
- **Concurrency:** 80 (по умолчанию)

**For High Load:**
- Увеличить memory до 8Gi
- Увеличить CPU до 4 cores
- Использовать Cloud Load Balancer

---

## 9. Troubleshooting

### 9.1 Common Issues

**Issue: Service fails to start**
- **Check:** Логи Cloud Run
- **Common causes:** Отсутствие секретов, неправильный MONGO_URI
- **Solution:** Проверить environment variables и secrets

**Issue: FAISS index not loading**
- **Check:** Логи при старте
- **Common causes:** Отсутствие embedding файлов
- **Solution:** Убедиться, что файлы включены в Docker image

**Issue: MongoDB connection timeout**
- **Check:** MongoDB Atlas network access
- **Common causes:** IP не в whitelist
- **Solution:** Добавить Cloud Run IP или использовать `0.0.0.0/0`

**Issue: YandexGPT API errors**
- **Check:** API ключ и folder ID
- **Common causes:** Неверный ключ, превышение лимитов
- **Solution:** Проверить ключ, увеличить лимиты в Yandex Cloud

### 9.2 Debug Commands

**View Logs:**
```bash
gcloud run services logs read financial-career-coach \
  --region us-central1 \
  --tail
```

**Check Service Status:**
```bash
gcloud run services describe financial-career-coach \
  --region us-central1
```

**Test Locally with Production Config:**
```bash
docker run -p 8080:8080 \
  --env-file .env.production \
  financial-career-coach:latest
```

---

## 10. Rollback

### 10.1 Rollback to Previous Revision

**1. List Revisions:**
```bash
gcloud run revisions list \
  --service financial-career-coach \
  --region us-central1
```

**2. Rollback:**
```bash
gcloud run services update-traffic financial-career-coach \
  --to-revisions REVISION_NAME=100 \
  --region us-central1
```

**3. Or Delete Latest Revision:**
```bash
gcloud run revisions delete REVISION_NAME \
  --region us-central1
```

---

## 11. CI/CD (Future)

### 11.1 GitHub Actions

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: google-github-actions/setup-gcloud@v0
      - run: gcloud builds submit --tag gcr.io/$PROJECT_ID/financial-career-coach
      - run: gcloud run deploy financial-career-coach --image gcr.io/$PROJECT_ID/financial-career-coach
```

### 11.2 Cloud Build Triggers

**1. Create Trigger:**
```bash
gcloud builds triggers create github \
  --repo-name=financial-career-coach \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

---

## 12. Cost Optimization

### 12.1 Current Costs

**Google Cloud Run:**
- Pay per request and CPU/memory usage
- Free tier: 2 million requests/month

**MongoDB Atlas:**
- Free tier: 512MB storage
- Paid: Starting from $9/month

**YandexGPT:**
- Pay per token
- Pricing: See Yandex Cloud documentation

### 12.2 Optimization Tips

1. **Scale to Zero:** Минимальные инстансы = 0 (экономия при отсутствии трафика)
2. **Memory Optimization:** Использовать минимально необходимое количество памяти
3. **Caching:** Кэширование LLM ответов (future)
4. **MongoDB:** Использовать индексы для быстрых запросов

---

## 13. Backup and Recovery

### 13.1 MongoDB Backups

**MongoDB Atlas:**
- Автоматические бэкапы (если включены)
- Ручной экспорт через `mongodump`

**Export Data:**
```bash
mongodump --uri="your-mongo-uri" --out=backup/
```

**Restore:**
```bash
mongorestore --uri="your-mongo-uri" backup/
```

### 13.2 Application Data

**Embeddings:**
- Хранятся в репозитории (`.npy` файлы)
- Резервное копирование через git

**Configuration:**
- Environment variables в Cloud Run
- Secrets в Secret Manager

---

**Document Status:** ✅ Complete



