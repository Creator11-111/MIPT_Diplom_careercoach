# 🔑 Подробная инструкция: Переменные окружения

## 📋 Что нужно настроить

Для работы карьерного коуча нужно настроить 5 переменных окружения:

1. `YANDEX_FOLDER_ID` - ID папки в Yandex Cloud
2. `YANDEX_API_KEY` - API ключ для YandexGPT
3. `MONGO_URI` - Строка подключения к MongoDB
4. `MONGO_DB` - Название базы данных
5. `APP_ENV` - Режим работы приложения

---

## 1️⃣ YANDEX_FOLDER_ID и YANDEX_API_KEY

### Что это?
Это ключи для работы с YandexGPT (AI модель для генерации ответов).

### Как получить:

#### Шаг 1: Регистрация в Yandex Cloud
1. Зайдите на https://cloud.yandex.ru/
2. Войдите через Яндекс аккаунт (или создайте новый)
3. Создайте платежный аккаунт (можно привязать карту, но есть бесплатный период)

#### Шаг 2: Создание каталога (Folder)
1. В консоли Yandex Cloud нажмите **"Каталоги"** (слева в меню)
2. Нажмите **"Создать каталог"**
3. Введите название: `career-coach` (или любое другое)
4. Нажмите **"Создать"**
5. **Скопируйте ID каталога** - это длинная строка вида `b1g1234567890abcdef` (это и есть `YANDEX_FOLDER_ID`)

#### Шаг 3: Создание сервисного аккаунта
1. В консоли Yandex Cloud перейдите в **"Сервисные аккаунты"** (слева в меню)
2. Нажмите **"Создать сервисный аккаунт"**
3. Введите название: `career-coach-service`
4. Выберите каталог, который создали выше
5. Нажмите **"Создать"**

#### Шаг 4: Назначение роли
1. Откройте созданный сервисный аккаунт
2. Перейдите на вкладку **"Роли"**
3. Нажмите **"Назначить роли"**
4. Выберите роль: **"AI Language Model User"** (или `ai.languageModels.user`)
5. Нажмите **"Сохранить"**

#### Шаг 5: Создание API ключа
1. В сервисном аккаунте перейдите на вкладку **"Ключи"**
2. Нажмите **"Создать ключ"** → **"API ключ"**
3. Нажмите **"Создать"**
4. **ВАЖНО! Скопируйте ключ сразу** - он показывается только один раз!
   - Ключ будет длинной строкой вида: `AQVNxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - Это и есть `YANDEX_API_KEY`

#### Шаг 6: Включение YandexGPT API
1. В консоли Yandex Cloud перейдите в **"API и сервисы"** → **"Каталог API"**
2. Найдите **"YandexGPT API"** (или "Yandex GPT")
3. Нажмите **"Подключить"**
4. Выберите каталог, который создали выше
5. Нажмите **"Подключить"**

### Итоговые значения:
```
YANDEX_FOLDER_ID=b1g1234567890abcdef
YANDEX_API_KEY=AQVNxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Где взять:**
- `YANDEX_FOLDER_ID` - ID каталога из шага 2
- `YANDEX_API_KEY` - API ключ из шага 5

---

## 2️⃣ MONGO_URI и MONGO_DB

### Что это?
Строка подключения к базе данных MongoDB (где хранятся вакансии, сессии, профили).

### Как получить:

#### Шаг 1: Регистрация в MongoDB Atlas
1. Зайдите на https://www.mongodb.com/cloud/atlas
2. Нажмите **"Try Free"** или **"Sign In"**
3. Войдите через Google/GitHub или создайте аккаунт

#### Шаг 2: Создание кластера
1. После входа нажмите **"Build a Database"**
2. Выберите план **"M0 FREE"** (бесплатный)
3. Выберите провайдера: **AWS** (или любой другой)
4. Выберите регион: ближайший к вам (например, `eu-central-1` для Европы)
5. Введите название кластера: `Cluster0` (или любое другое)
6. Нажмите **"Create"**
7. Дождитесь создания кластера (2-3 минуты)

#### Шаг 3: Создание пользователя базы данных
1. В появившемся окне **"Create Database User"**:
   - **Username**: `careercoach` (или любое другое)
   - **Password**: придумайте надежный пароль (запомните его!)
   - Нажмите **"Create User"**

#### Шаг 4: Настройка доступа по сети
1. В разделе **"Network Access"** нажмите **"Add IP Address"**
2. Для тестирования выберите **"Allow Access from Anywhere"** (добавит `0.0.0.0/0`)
   - ⚠️ Для продакшена лучше добавить конкретный IP Railway/Render
3. Нажмите **"Confirm"**

#### Шаг 5: Получение connection string
1. В главном окне кластера нажмите **"Connect"**
2. Выберите **"Connect your application"**
3. Выберите драйвер: **Python** и версию: **3.12 or later**
4. Скопируйте connection string - он будет вида:
   ```
   mongodb+srv://careercoach:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. **Замените `<password>` на ваш пароль** из шага 3
6. **Добавьте название базы данных** в конце:
   ```
   mongodb+srv://careercoach:ваш_пароль@cluster0.xxxxx.mongodb.net/financial_career_coach?retryWrites=true&w=majority
   ```

### Итоговые значения:
```
MONGO_URI=mongodb+srv://careercoach:ваш_пароль@cluster0.xxxxx.mongodb.net/financial_career_coach?retryWrites=true&w=majority
MONGO_DB=financial_career_coach
```

**Где взять:**
- `MONGO_URI` - connection string из шага 5 (с замененным паролем и названием БД)
- `MONGO_DB` - просто `financial_career_coach` (название базы данных)

---

## 3️⃣ APP_ENV

### Что это?
Режим работы приложения (development/production).

### Значение:
```
APP_ENV=production
```

**Просто укажите:** `production` (для работы на сервере)

---

## 📝 Пример заполнения всех переменных

После получения всех значений, в Railway/Render добавьте:

```
YANDEX_FOLDER_ID=b1g1234567890abcdef
YANDEX_API_KEY=AQVNxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
MONGO_URI=mongodb+srv://careercoach:мой_пароль123@cluster0.abc123.mongodb.net/financial_career_coach?retryWrites=true&w=majority
MONGO_DB=financial_career_coach
APP_ENV=production
```

---

## ⚠️ Важные замечания

1. **YANDEX_API_KEY** показывается только один раз! Сохраните его сразу.
2. **Пароль MongoDB** - замените `<password>` в connection string на реальный пароль.
3. **Безопасность**: Никогда не коммитьте эти значения в Git!
4. **Бесплатные тарифы**: 
   - MongoDB Atlas M0 - бесплатный (512 MB)
   - Yandex Cloud - есть бесплатный период

---

## 🔍 Проверка настроек

После добавления переменных в Railway/Render:

1. Проверьте логи деплоя - не должно быть ошибок подключения
2. Откройте `https://your-url/health` - должно быть `{"status":"ok"}`
3. Попробуйте отправить сообщение в чат - должно работать

---

## ❓ Проблемы?

### Ошибка "YandexGPT not configured"
- Проверьте, что `YANDEX_FOLDER_ID` и `YANDEX_API_KEY` указаны правильно
- Убедитесь, что API ключ действителен
- Проверьте, что YandexGPT API подключен в каталоге

### Ошибка подключения к MongoDB
- Проверьте, что IP сервера добавлен в Network Access
- Убедитесь, что пароль правильный в connection string
- Проверьте, что кластер запущен

### Ошибка "Database connection failed"
- Проверьте формат `MONGO_URI` (должен начинаться с `mongodb+srv://`)
- Убедитесь, что название базы данных указано в URI

---

**Готово! Теперь вы знаете, как получить все необходимые значения.** 🎉



