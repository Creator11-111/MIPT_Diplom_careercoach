# 📤 Инструкция: Загрузка проекта в GitHub и настройка автосинхронизации

## Шаг 1: Подготовка

1. Откройте **командную строку** (Win+R → введите `cmd` → Enter)

2. Перейдите в папку проекта:
   ```cmd
   cd /d "E:\Project_career coach\career-couch1\financial_coach"
   ```

## Шаг 2: Инициализация Git (если еще не сделано)

```cmd
git init
```

## Шаг 3: Добавление всех файлов

```cmd
git add .
```

## Шаг 4: Создание первого коммита

```cmd
git commit -m "Initial commit: Financial Career Coach"
```

## Шаг 5: Создание ветки

```cmd
git branch -M diploma-version
```

## Шаг 6: Подключение к GitHub

```cmd
git remote add origin https://github.com/Creator11-111/MIPT_Diplom_careercoach.git
```

**Если репозиторий уже был подключен, сначала удалите старый:**
```cmd
git remote remove origin
git remote add origin https://github.com/Creator11-111/MIPT_Diplom_careercoach.git
```

## Шаг 7: Загрузка в GitHub

```cmd
git push -u origin diploma-version
```

**При запросе введите:**
- **Логин GitHub** (ваш username)
- **Пароль** ИЛИ **Personal Access Token** (если включена двухфакторная аутентификация)

### Как создать Personal Access Token:

1. Откройте: https://github.com/settings/tokens
2. Нажмите **"Generate new token"** → **"Generate new token (classic)"**
3. Название: `Career Coach Sync`
4. Срок действия: выберите нужный (например, 90 дней)
5. Права: отметьте **`repo`** (полный доступ к репозиториям)
6. Нажмите **"Generate token"**
7. **СКОПИРУЙТЕ токен** (он показывается только один раз!)
8. Вставьте токен вместо пароля при запросе

## Шаг 8: Настройка автоматической синхронизации

После успешной загрузки выполните:

```cmd
mkdir .git\hooks
```

Затем создайте файл `.git\hooks\post-commit.bat` со следующим содержимым:

```batch
@echo off
git push origin diploma-version
```

**Или выполните команду:**
```cmd
echo @echo off > .git\hooks\post-commit.bat
echo git push origin diploma-version >> .git\hooks\post-commit.bat
```

## ✅ Готово!

Теперь:
- Проект загружен в GitHub: https://github.com/Creator11-111/MIPT_Diplom_careercoach
- При каждом коммите изменения автоматически отправляются в GitHub

## 📝 Как использовать автосинхронизацию:

После любых изменений в коде выполните:

```cmd
git add .
git commit -m "Описание изменений"
```

Изменения автоматически отправятся в GitHub!

---

## 🔧 Если что-то пошло не так:

### Ошибка "repository not found":
- Убедитесь, что репозиторий существует на GitHub
- Проверьте, что у вас есть доступ к репозиторию

### Ошибка "authentication failed":
- Используйте Personal Access Token вместо пароля
- Убедитесь, что токен имеет права `repo`

### Ошибка "remote origin already exists":
- Выполните: `git remote remove origin`
- Затем снова: `git remote add origin https://github.com/Creator11-111/MIPT_Diplom_careercoach.git`

### Изменения не отправляются автоматически:
- Проверьте, что файл `.git\hooks\post-commit.bat` существует
- Попробуйте выполнить `git push origin diploma-version` вручную

