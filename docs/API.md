# API Documentation

**Date:** 2025-01-12  
**Version:** 1.0.0  
**Base URL:** `https://your-domain.run.app/v1`

---

## 1. Overview

API использует REST архитектуру и JSON для обмена данными. Все endpoints (кроме health checks) имеют префикс `/v1/`.

### 1.1 Authentication

В текущей версии API не требует аутентификации. Все endpoints доступны публично.

### 1.2 Rate Limiting

- **Лимит:** 100 запросов в минуту на IP-адрес
- **Window:** 60 секунд
- **Response при превышении:** `429 Too Many Requests`

### 1.3 Error Format

Все ошибки возвращаются в формате:
```json
{
  "detail": "Error message"
}
```

### 1.4 Health Endpoints

Эти endpoints находятся на корневом уровне (без `/v1/`):

- `GET /health` - Проверка работоспособности
- `GET /ready` - Проверка готовности системы
- `GET /debug` - Отладочная информация

---

## 2. Sessions API

### 2.1 Create Session

**Endpoint:** `POST /v1/sessions`

**Description:** Создает новую сессию чата с автоматическим приветствием.

**Request Body:**
```json
{
  "user_id": "optional-user-id"  // Опционально, если не указан - генерируется автоматически
}
```

**Response:** `200 OK`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-123"
}
```

**Example:**
```bash
curl -X POST https://your-domain.run.app/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123"}'
```

---

### 2.2 Get Session

**Endpoint:** `GET /v1/sessions/{session_id}`

**Description:** Получает сессию с историей сообщений.

**Path Parameters:**
- `session_id` (string, required) - ID сессии

**Response:** `200 OK`
```json
{
  "session": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user-123",
    "state": {
      "last_question_type": null,
      "last_updated_at": "2025-01-12T10:00:00"
    }
  },
  "messages": [
    {
      "message_id": "msg-1",
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "role": "assistant",
      "content": "Здравствуйте! Я задам вам около 8-10 вопросов...",
      "created_at": "2025-01-12T10:00:00",
      "done": false
    }
  ]
}
```

**Errors:**
- `404 Not Found` - Сессия не найдена

---

### 2.3 List Sessions

**Endpoint:** `GET /v1/sessions?user_id={user_id}`

**Description:** Получает список всех сессий пользователя.

**Query Parameters:**
- `user_id` (string, optional) - ID пользователя

**Response:** `200 OK`
```json
{
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": "user-123",
      "last_updated_at": "2025-01-12T10:00:00",
      "preview": "💼 Поиск работы • Здравствуйте! Я задам вам..."
    }
  ]
}
```

**Example:**
```bash
curl "https://your-domain.run.app/v1/sessions?user_id=user-123"
```

---

### 2.4 Delete Session

**Endpoint:** `DELETE /v1/sessions/{session_id}`

**Description:** Удаляет сессию и все её сообщения.

**Path Parameters:**
- `session_id` (string, required) - ID сессии

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Session deleted successfully"
}
```

**Errors:**
- `404 Not Found` - Сессия не найдена

---

### 2.5 Export Session

**Endpoint:** `GET /v1/sessions/{session_id}/export?format={format}`

**Description:** Экспортирует историю сессии в PDF или Word.

**Path Parameters:**
- `session_id` (string, required) - ID сессии

**Query Parameters:**
- `format` (string, optional) - Формат экспорта: `pdf` или `docx` (default: `pdf`)

**Response:** `200 OK`
- Content-Type: `application/pdf` или `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- Content-Disposition: `attachment; filename="chat_history_{session_id}.pdf"`

**Example:**
```bash
curl "https://your-domain.run.app/v1/sessions/{session_id}/export?format=pdf" \
  --output chat_history.pdf
```

---

## 3. Chat API

### 3.1 Send Message

**Endpoint:** `POST /v1/chat/{session_id}`

**Description:** Отправляет сообщение пользователя и получает ответ AI.

**Path Parameters:**
- `session_id` (string, required) - ID сессии

**Request Body:**
```json
{
  "text": "Я работаю финансовым аналитиком в банке уже 5 лет."
}
```

**Response:** `200 OK`
```json
{
  "reply": "Отлично! Расскажите, пожалуйста, какие финансовые инструменты вы используете в работе?",
  "done": false
}
```

**Response Fields:**
- `reply` (string) - Ответ AI
- `done` (boolean) - Флаг завершенности интервью

**Errors:**
- `400 Bad Request` - Пустое сообщение или слишком длинное (>5000 символов)
- `404 Not Found` - Сессия не найдена
- `503 Service Unavailable` - YandexGPT API недоступен

**Example:**
```bash
curl -X POST https://your-domain.run.app/v1/chat/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{"text": "Я работаю финансовым аналитиком в банке уже 5 лет."}'
```

---

## 4. Profile API

### 4.1 Build Profile

**Endpoint:** `GET /v1/profile/{session_id}`

**Description:** Строит структурированный профиль из истории диалога.

**Path Parameters:**
- `session_id` (string, required) - ID сессии

**Response:** `200 OK`
```json
{
  "profile": {
    "professional_context": {
      "professional_role": "Финансовый аналитик",
      "professional_field": "Банки",
      "specialization": "Финансовый анализ",
      "seniority_level": "middle"
    },
    "resume": [
      {
        "title": "Финансовый аналитик",
        "company": "Банк ВТБ",
        "duration_years": 5,
        "tasks": ["Анализ финансовых показателей", "Подготовка отчетности"],
        "tech_stack": ["Excel", "1С", "SAP"]
      }
    ],
    "skills": {
      "hard_skills": ["Финансовый анализ", "МСФО", "Бюджетирование"],
      "tools": ["Excel", "1С", "SAP", "Bloomberg Terminal"],
      "soft_skills": ["Аналитическое мышление", "Работа в команде"]
    },
    "goals": {
      "desired_role": "CFO",
      "target_field": "Корпоративные финансы",
      "target_specialization": "Финансовое управление"
    },
    "achievements": [
      "Повышение эффективности бюджетирования на 20%",
      "Внедрение системы МСФО"
    ]
  }
}
```

**Errors:**
- `404 Not Found` - Сессия не найдена или недостаточно данных для построения профиля
- `503 Service Unavailable` - YandexGPT API недоступен

**Example:**
```bash
curl "https://your-domain.run.app/v1/profile/550e8400-e29b-41d4-a716-446655440000"
```

---

### 4.2 Get Profile by User ID

**Endpoint:** `GET /v1/profile/by-user/{user_id}`

**Description:** Получает профиль пользователя по user_id (из любой сессии).

**Path Parameters:**
- `user_id` (string, required) - ID пользователя

**Response:** `200 OK`
```json
{
  "profile": {
    // Same structure as Build Profile
  }
}
```

**Errors:**
- `404 Not Found` - Профиль не найден

**Example:**
```bash
curl "https://your-domain.run.app/v1/profile/by-user/user-123"
```

---

## 5. Match API

### 5.1 Match Vacancies

**Endpoint:** `POST /v1/match/vacancies/by-session/{session_id}`

**Description:** Находит релевантные вакансии на основе профиля из сессии.

**Path Parameters:**
- `session_id` (string, required) - ID сессии

**Request Body:**
```json
{
  "k_faiss": 100,    // Количество кандидатов из FAISS (default: 100)
  "k_stage1": 30,    // Количество после Stage 1 фильтрации (default: 30)
  "k_stage2": 15     // Финальное количество вакансий (default: 15)
}
```

**Response:** `200 OK`
```json
{
  "result": [
    {
      "idx": 1234,
      "title": "Финансовый аналитик",
      "company": "Банк ВТБ",
      "location": "Москва",
      "salary": "150 000 - 250 000 руб.",
      "experience": "3-6 лет",
      "description": "Анализ финансовых показателей, подготовка отчетности...",
      "key_skills": "Excel, 1С, SAP, МСФО",
      "hh_url": "https://hh.ru/vacancy/1234",
      "match_score": 0.89
    }
  ]
}
```

**Response Fields:**
- `result` (array) - Список вакансий, отсортированных по релевантности
- `match_score` (float) - Оценка релевантности (0-1)

**Errors:**
- `404 Not Found` - Сессия не найдена или профиль не построен
- `503 Service Unavailable` - YandexGPT API или FAISS недоступен

**Example:**
```bash
curl -X POST https://your-domain.run.app/v1/match/vacancies/by-session/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{"k_faiss": 100, "k_stage1": 30, "k_stage2": 15}'
```

---

### 5.2 Career Development Plan

**Endpoint:** `POST /v1/match/career-development`

**Description:** Создает план развития карьеры с анализом разрывов, курсами и вакансиями.

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "target_position": "CFO",
  "target_field": "Корпоративные финансы",
  "target_specialization": "Финансовое управление"
}
```

**Response:** `200 OK`
```json
{
  "gap_analysis": "Для перехода на позицию CFO необходимо развить:\n1. Стратегическое мышление\n2. Управление командой\n...",
  "courses": [
    {
      "name": "MBA Финансы",
      "provider": "Нетология",
      "description": "Комплексная программа по финансовому управлению",
      "skills": "Стратегическое планирование, управление",
      "url": "https://netology.ru/...",
      "required": true
    }
  ],
  "future_vacancies": [
    {
      "idx": 5678,
      "title": "Финансовый менеджер",
      "company": "Компания X",
      "hh_url": "https://hh.ru/vacancy/5678",
      "match_score": 0.85
    }
  ]
}
```

**Response Fields:**
- `gap_analysis` (string) - Анализ разрывов в навыках
- `courses` (array) - Рекомендуемые курсы
- `future_vacancies` (array) - Промежуточные вакансии на пути к цели

**Errors:**
- `404 Not Found` - Сессия не найдена или профиль не построен
- `400 Bad Request` - Не указана целевая позиция
- `503 Service Unavailable` - YandexGPT API недоступен

**Example:**
```bash
curl -X POST https://your-domain.run.app/v1/match/career-development \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "target_position": "CFO",
    "target_field": "Корпоративные финансы"
  }'
```

---

## 6. Health Check Endpoints

### 6.1 Health

**Endpoint:** `GET /health`

**Description:** Простая проверка работоспособности приложения.

**Response:** `200 OK`
```json
{
  "status": "ok",
  "time": "2025-01-12T10:00:00"
}
```

---

### 6.2 Ready

**Endpoint:** `GET /ready`

**Description:** Проверка готовности системы (MongoDB, FAISS).

**Response:** `200 OK`
```json
{
  "ready": true,
  "faiss_built": true,
  "vacancies_count": 2574,
  "mongo_connected": true
}
```

**Response Fields:**
- `ready` (boolean) - Общая готовность системы
- `faiss_built` (boolean) - FAISS индекс построен
- `vacancies_count` (int) - Количество вакансий в индексе
- `mongo_connected` (boolean) - MongoDB подключена

---

### 6.3 Debug

**Endpoint:** `GET /debug`

**Description:** Отладочная информация о системе.

**Response:** `200 OK`
```json
{
  "ready": true,
  "port": 8080,
  "faiss": {
    "built": true,
    "vacancies_count": 2574,
    "dimension": 256
  },
  "mongo": {
    "connected": true,
    "database": "financial_coach"
  }
}
```

---

## 7. Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Неверные параметры запроса |
| 404 | Not Found - Ресурс не найден |
| 429 | Too Many Requests - Превышен лимит запросов |
| 500 | Internal Server Error - Внутренняя ошибка сервера |
| 503 | Service Unavailable - Внешний сервис недоступен |

---

## 8. Rate Limiting

**Лимит:** 100 запросов в минуту на IP-адрес

**Headers:**
- `Retry-After: 60` - Время до следующего запроса (в секундах)

**Response при превышении:**
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

---

## 9. CORS

CORS настраивается через переменную окружения `CORS_ORIGINS`.

**Пример:**
```
CORS_ORIGINS=https://example.com,https://another-domain.com
```

Для разработки можно использовать `*` (не рекомендуется для production).

---

## 10. API Versioning

Все API endpoints имеют префикс `/v1/`. Health check endpoints находятся на корневом уровне.

**Примеры:**
- ✅ `POST /v1/sessions`
- ✅ `GET /v1/chat/{session_id}`
- ✅ `GET /health` (без версии)

---

## 11. Request/Response Examples

### 11.1 Complete Flow: Profile Creation

```bash
# 1. Create session
SESSION_RESPONSE=$(curl -X POST https://your-domain.run.app/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123"}')

SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.session_id')

# 2. Send messages
curl -X POST https://your-domain.run.app/v1/chat/$SESSION_ID \
  -H "Content-Type: application/json" \
  -d '{"text": "Я работаю финансовым аналитиком в банке уже 5 лет."}'

# 3. Build profile
curl "https://your-domain.run.app/v1/profile/$SESSION_ID"

# 4. Get vacancies
curl -X POST https://your-domain.run.app/v1/match/vacancies/by-session/$SESSION_ID \
  -H "Content-Type: application/json" \
  -d '{"k_faiss": 100, "k_stage1": 30, "k_stage2": 15}'
```

---

**Document Status:** ✅ Complete



