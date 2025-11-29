# 🔧 Исправление ошибки деплоя на Railway

## ❌ Проблема

Ошибка: `cd: financial_coach: No such file or directory`

Это происходит потому, что Railway не знает, где находится папка `financial_coach` в репозитории.

## ✅ Решение

### Вариант 1: Указать Root Directory в Railway (Рекомендуется)

1. В Railway откройте ваш проект
2. Перейдите в **Settings** → **Service**
3. Найдите раздел **"Root Directory"**
4. Укажите: `financial_coach`
5. Сохраните изменения
6. Railway автоматически перезапустит деплой

### Вариант 2: Изменить команду запуска

Если Root Directory недоступен, измените команду запуска:

1. В Railway откройте ваш проект
2. Перейдите в **Settings** → **Deploy**
3. Найдите **"Start Command"**
4. Измените на:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
   (уберите `cd financial_coach &&`)
5. Сохраните изменения

### Вариант 3: Обновить railway.json

Если структура репозитория другая, обновите `railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

## 🔍 Проверка структуры репозитория

Убедитесь, что в GitHub репозитории структура такая:

```
MIPT_Diplom_careercoach/
  └── financial_coach/
      ├── app/
      ├── data/
      ├── static/
      ├── requirements.txt
      ├── Procfile
      └── railway.json
```

Если структура другая (например, файлы в корне репозитория), нужно либо:
- Переместить файлы в папку `financial_coach`
- Или изменить команды запуска

---

## 📝 Быстрое исправление

**Самый простой способ:**

1. В Railway → Settings → Service
2. Установите **Root Directory**: `financial_coach`
3. Сохраните
4. Дождитесь перезапуска

После этого команда `cd financial_coach && ...` не нужна, так как Railway уже будет работать из папки `financial_coach`.

