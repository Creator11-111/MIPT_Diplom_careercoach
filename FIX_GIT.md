# 🔧 Исправление: Правильная настройка Git для financial_coach

## Проблема
Git был инициализирован в родительской папке `career-couch1`, а не в `financial_coach`.

## Решение

Выполните команды в PowerShell **в папке financial_coach**:

```powershell
# 1. Перейдите в папку financial_coach
cd "E:\Project_career coach\career-couch1\financial_coach"

# 2. Инициализируйте Git (если еще не инициализирован)
git init

# 3. Добавьте все файлы
git add .

# 4. Создайте первый коммит
git commit -m "Initial commit: Financial Career Coach"

# 5. Создайте ветку
git branch -M diploma-version

# 6. Настройте remote (удалите старый, если есть)
git remote remove origin
git remote add origin https://github.com/Creator11-111/MIPT_Diplom_careercoach.git

# 7. Загрузите в GitHub
git push -u origin diploma-version
```

## Настройка автоматической синхронизации

После успешной загрузки выполните:

```powershell
# Создайте папку для хуков (если не существует)
New-Item -ItemType Directory -Force -Path .git\hooks

# Создайте файл post-commit.bat
@"
@echo off
git push origin diploma-version
"@ | Out-File -FilePath .git\hooks\post-commit.bat -Encoding ASCII
```

Теперь при каждом коммите изменения будут автоматически отправляться в GitHub!

