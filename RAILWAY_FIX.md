# 🔧 Быстрое исправление ошибки Railway

## ❌ Проблема
```
/bin/bash: line 1: cd: financial_coach: No such file or directory
```

## ✅ Решение (2 способа)

### Способ 1: Указать Root Directory в Railway (РЕКОМЕНДУЕТСЯ)

1. В Railway откройте ваш проект
2. Перейдите в **Settings** → **Service**
3. Найдите раздел **"Root Directory"**
4. Укажите: `financial_coach`
5. Нажмите **"Save"**
6. Railway автоматически перезапустит деплой

**После этого команда запуска будет работать из папки `financial_coach` автоматически!**

---

### Способ 2: Обновить файлы (если Root Directory недоступен)

Я уже обновил файлы `railway.json` и `Procfile` - убрал `cd financial_coach &&` из команд.

Теперь нужно:

1. **Закоммитьте изменения:**
   ```powershell
   git add railway.json Procfile
   git commit -m "Fix Railway deploy: remove cd command"
   ```
   (Изменения автоматически отправятся в GitHub)

2. **В Railway:**
   - Перейдите в **Settings** → **Service**
   - Установите **Root Directory**: `financial_coach`
   - Или оставьте пустым, если файлы в корне репозитория

3. **Railway автоматически перезапустит деплой**

---

## 🔍 Проверка структуры репозитория

Убедитесь, что в GitHub структура такая:

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

Если структура другая (файлы в корне), то:
- Либо установите Root Directory = `financial_coach`
- Либо переместите файлы в папку `financial_coach`

---

## ✅ После исправления

После применения одного из способов, Railway должен успешно запустить приложение!

Проверьте логи - должно быть:
```
INFO:     Uvicorn running on http://0.0.0.0:XXXX
```

