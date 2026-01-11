# Data Flow Documentation

**Date:** 2025-01-12  
**Version:** 1.0.0

---

## 1. Overview

Документ описывает потоки данных в системе Financial Career Coach, включая последовательности операций, преобразования данных и взаимодействия между компонентами.

---

## 2. Profile Creation Data Flow

### 2.1 Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant SR as SessionsRouter
    participant CR as ChatRouter
    participant CS as ChatService
    participant MR as MessagesRepo
    participant YGPT as YandexGPT
    participant PR as ProfilesRepo
    participant DB as MongoDB
    
    Note over U,DB: Шаг 1: Создание сессии
    U->>F: Нажимает "Хочу найти работу"
    F->>SR: POST /v1/sessions
    SR->>DB: Создать session document
    DB-->>SR: session_id
    SR-->>F: {session_id, user_id}
    F->>F: Сохранить session_id в localStorage
    
    Note over U,DB: Шаг 2: Диалог (8-10 вопросов)
    loop Для каждого вопроса
        U->>F: Отправляет ответ
        F->>CR: POST /v1/chat/{session_id}
        CR->>MR: Загрузить историю (limit=40)
        MR->>DB: find({session_id})
        DB-->>MR: messages[]
        MR-->>CR: messages
        
        CR->>CS: generate_reply(session_id, text)
        CS->>MR: list_by_session()
        MR-->>CS: chat_messages[]
        
        CS->>CS: build_messages_payload()
        CS->>YGPT: Structured completion
        Note over YGPT: Промпт: CHAT_SYSTEM_PROMPT<br/>Схема: {answer, done}
        YGPT-->>CS: {answer: "...", done: false}
        
        CS->>MR: insert_one(user_message)
        CS->>MR: insert_one(assistant_message)
        MR->>DB: insert messages
        CS-->>CR: ChatResponse
        CR-->>F: {reply, done}
        F-->>U: Отобразить ответ AI
    end
    
    Note over U,DB: Шаг 3: Построение профиля
    U->>F: Нажимает "Профиль"
    F->>PR: GET /v1/profile/{session_id}
    PR->>CS: build_profile(session_id)
    CS->>MR: get_all_by_session()
    MR->>DB: find({session_id})
    DB-->>MR: all_messages[]
    MR-->>CS: messages[]
    
    CS->>CS: Формирование промпта
    Note over CS: PROFILE_SYSTEM_PROMPT<br/>+ Требование максимальной детализации
    
    CS->>YGPT: Structured completion
    Note over YGPT: Схема: UserProfile JSON
    YGPT-->>CS: JSON профиль
    
    CS->>CS: Валидация через Pydantic
    CS->>PR: insert_one(profile)
    PR->>DB: insert profile document
    CS-->>PR: UserProfile
    PR-->>F: {profile: {...}}
    F-->>U: Отобразить профиль
```

### 2.2 Data Transformations

**Input:** Свободный текст в диалоге
```
User: "Я работаю финансовым аналитиком в банке уже 5 лет. 
       Использую Excel, 1С, SAP. Прошел курсы по МСФО."
```

**Processing:**
1. Сохранение в MongoDB как есть
2. Агрегация всей истории диалога
3. Отправка в YandexGPT с промптом

**Output:** Структурированный JSON профиль
```json
{
  "professional_context": {
    "professional_role": "Финансовый аналитик",
    "professional_field": "Банки",
    "seniority_level": "middle"
  },
  "resume": [{
    "title": "Финансовый аналитик",
    "company": "Банк",
    "duration_years": 5,
    "tech_stack": ["Excel", "1С", "SAP"]
  }],
  "skills": {
    "hard_skills": ["Финансовый анализ", "МСФО"],
    "tools": ["Excel", "1С", "SAP"]
  }
}
```

---

## 3. Job Matching Data Flow

### 3.1 Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant MR as MatchRouter
    participant MS as MatchService
    participant YGPT as YandexGPT
    participant FAISS as FAISS Index
    participant VR as VacanciesRepo
    participant DB as MongoDB
    
    U->>F: Нажимает "Вакансии"
    F->>MR: POST /v1/match/vacancies/by-session/{id}
    
    MR->>MR: Получить профиль из сессии
    MR->>MS: match_vacancies(resume_text)
    
    Note over MS,YGPT: Этап 0: Препроцессинг
    MS->>YGPT: Препроцессинг резюме
    Note over YGPT: Обогащение ключевыми словами
    YGPT-->>MS: Обогащенное резюме
    
    Note over MS,YGPT: Этап 1: Создание эмбеддинга
    MS->>YGPT: embed_text(resume)
    YGPT-->>MS: Query embedding (256 dim)
    
    Note over MS,FAISS: Этап 2: FAISS поиск
    MS->>FAISS: search_top_k(query_vec, k=100)
    FAISS-->>MS: [idx1, idx2, ..., idx100]
    
    Note over MS,DB: Этап 3: Загрузка вакансий
    MS->>VR: find_by_ids([idx1, ..., idx100])
    VR->>DB: find({idx: {$in: [...]}})
    DB-->>VR: vacancies[]
    VR-->>MS: ordered_vacancies[]
    
    Note over MS,YGPT: Этап 4: Stage 1 фильтрация
    MS->>MS: Формирование списка названий
    MS->>YGPT: Structured completion
    Note over YGPT: Промпт: MATCH_SYSTEM_PROMPT_STAGE1<br/>Схема: {selected: [idx]}
    YGPT-->>MS: {selected: [idx1, idx5, ..., idx30]}
    
    Note over MS,YGPT: Этап 5: Stage 2 фильтрация
    MS->>MS: Формирование детальных описаний
    MS->>YGPT: Structured completion
    Note over YGPT: Промпт: MATCH_SYSTEM_PROMPT_STAGE2<br/>Схема: {selected: [idx]}
    YGPT-->>MS: {selected: [idx1, idx3, ..., idx15]}
    
    MS->>MS: Формирование финального списка
    MS-->>MR: MatchVacanciesResponse
    MR-->>F: {result: [vacancy1, ..., vacancy15]}
    F-->>U: Отобразить 15 вакансий
```

### 3.2 Data Transformations

**Input:** Текст резюме из профиля
```
"Финансовый аналитик в банке, 5 лет опыта, 
Excel, 1С, SAP, курсы МСФО"
```

**Step 1: Препроцессинг**
```
"Финансовый аналитик в банковском секторе, 
5 лет опыта в финансовом анализе, 
работа с Excel (продвинутый уровень), 
1С:Бухгалтерия, SAP ERP, 
сертификаты по МСФО (Международные стандарты финансовой отчетности)"
```

**Step 2: Эмбеддинг**
```
[0.123, -0.456, 0.789, ..., 0.234] (256 dimensions)
```

**Step 3: FAISS Search**
```
Cosine similarity scores:
idx1: 0.89
idx2: 0.87
...
idx100: 0.65
```

**Step 4: LLM Filtering**
```
Stage 1: [idx1, idx5, idx12, ..., idx30] (30 вакансий)
Stage 2: [idx1, idx5, idx12, ..., idx15] (15 вакансий)
```

**Output:** Список вакансий с метаданными
```json
{
  "result": [
    {
      "idx": 1234,
      "title": "Финансовый аналитик",
      "company": "Банк ВТБ",
      "match_score": 0.89,
      "hh_url": "https://hh.ru/vacancy/1234"
    },
    ...
  ]
}
```

---

## 4. Career Development Data Flow

### 4.1 Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant MR as MatchRouter
    participant CDS as CareerDevService
    participant PS as ProfileService
    participant MS as MatchService
    participant YGPT as YandexGPT
    participant FAISS as FAISS Index
    participant DB as MongoDB
    
    U->>F: Описывает цель: "Хочу стать CFO"
    F->>MR: POST /v1/match/career-development
    
    MR->>CDS: create_development_plan(session_id, target)
    
    Note over CDS,DB: Шаг 1: Получение профиля
    CDS->>PS: Получить профиль
    PS->>DB: Загрузить профиль
    DB-->>PS: Profile
    PS-->>CDS: UserProfile
    
    Note over CDS,YGPT: Шаг 2: Gap Analysis
    CDS->>CDS: _build_resume_from_profile()
    CDS->>YGPT: Text completion
    Note over YGPT: Промпт: CAREER_GAP_ANALYSIS_PROMPT
    YGPT-->>CDS: Gap analysis text
    
    Note over CDS,YGPT: Шаг 3: Подбор курсов
    CDS->>YGPT: Text completion
    Note over YGPT: Промпт: COURSE_RECOMMENDATIONS_PROMPT<br/>Схема: Course JSON
    YGPT-->>CDS: Courses list
    
    Note over CDS,YGPT: Шаг 4: Будущее резюме
    CDS->>YGPT: Text completion
    Note over YGPT: Промпт: FUTURE_VACANCIES_PROMPT
    YGPT-->>CDS: Future resume text
    
    Note over CDS,FAISS: Шаг 5: Поиск вакансий
    CDS->>MS: match_vacancies(future_resume)
    MS->>FAISS: Поиск
    MS->>YGPT: Фильтрация
    MS-->>CDS: Future vacancies (15)
    
    CDS->>CDS: Формирование ответа
    CDS-->>MR: CareerDevelopmentResponse
    MR-->>F: {gap_analysis, courses, future_vacancies}
    F-->>U: Отобразить план развития
```

### 4.2 Data Transformations

**Input 1:** Текущий профиль
```json
{
  "professional_context": {
    "professional_role": "Финансовый аналитик",
    "seniority_level": "middle"
  },
  "skills": {
    "hard_skills": ["Excel", "1С", "МСФО"]
  }
}
```

**Input 2:** Целевая позиция
```
"Финансовый директор (CFO)"
```

**Step 1: Gap Analysis**
```
"Для перехода на позицию CFO необходимо развить:
1. Стратегическое мышление
2. Управление командой
3. Финансовое планирование и бюджетирование
4. Работа с инвесторами
5. Знание корпоративных финансов"
```

**Step 2: Курсы**
```json
[
  {
    "name": "MBA Финансы",
    "provider": "Нетология",
    "skills": "Стратегическое планирование, управление",
    "url": "https://netology.ru/..."
  },
  ...
]
```

**Step 3: Будущее резюме**
```
"Финансовый менеджер с опытом стратегического планирования,
управления командой, работы с бюджетами.
Прошел курсы MBA Финансы, управление проектами.
Готов к переходу на позицию CFO."
```

**Step 4: Промежуточные вакансии**
```
[Вакансия: Финансовый менеджер, Вакансия: Заместитель CFO, ...]
```

**Output:** Полный план развития
```json
{
  "gap_analysis": "...",
  "courses": [...],
  "future_vacancies": [...]
}
```

---

## 5. Skills Analysis Data Flow

### 5.1 Flow Description

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant CR as ChatRouter
    participant CS as ChatService
    participant YGPT as YandexGPT
    participant DB as MongoDB
    
    U->>F: Указывает позицию: "CFO"
    F->>CR: POST /v1/chat/{session_id}
    
    CR->>CS: generate_reply()
    CS->>CS: Проверка: есть ли профиль?
    CS->>DB: Загрузить профиль
    DB-->>CS: Profile
    
    CS->>CS: Формирование детального промпта
    Note over CS: SKILLS_ANALYSIS_SYSTEM_PROMPT<br/>+ Текущий профиль<br/>+ Целевая позиция
    
    CS->>YGPT: Text completion
    Note over YGPT: Детальный анализ навыков:<br/>1. Навыки которые есть<br/>2. Навыки которые нужно развить<br/>3. План развития<br/>4. Рекомендации
    YGPT-->>CS: Детальный анализ
    
    CS->>DB: Сохранить сообщение
    CS-->>CR: ChatResponse
    CR-->>F: {reply: "..."}
    F-->>U: Отобразить анализ
```

---

## 6. Goals Analysis Data Flow

### 6.1 Flow Description

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant CR as ChatRouter
    participant CS as ChatService
    participant YGPT as YandexGPT
    participant DB as MongoDB
    
    U->>F: Описывает цели
    F->>CR: POST /v1/chat/{session_id}
    
    CR->>CS: generate_reply()
    CS->>DB: Загрузить профиль
    DB-->>CS: Profile
    
    CS->>CS: Формирование промпта
    Note over CS: GOALS_ANALYSIS_SYSTEM_PROMPT<br/>+ Текущий профиль<br/>+ Описание целей
    
    CS->>YGPT: Text completion
    Note over YGPT: Комплексный анализ:<br/>1. SWOT-анализ<br/>2. Реалистичность<br/>3. Пошаговый план<br/>4. Альтернативные пути<br/>5. Временная дорожная карта
    YGPT-->>CS: Детальный анализ целей
    
    CS->>DB: Сохранить
    CS-->>CR: ChatResponse
    CR-->>F: {reply: "..."}
    F-->>U: Отобразить анализ
```

---

## 7. Data Storage Flow

### 7.1 Write Operations

```mermaid
graph LR
    A[User Input] --> B[Router]
    B --> C[Service]
    C --> D[Repository]
    D --> E[(MongoDB)]
    
    E --> F[Index Update]
    F --> G[Response]
```

**Пример: Сохранение сообщения**
1. User отправляет сообщение
2. Router валидирует через Pydantic
3. Service обрабатывает
4. Repository вставляет в MongoDB
5. MongoDB создает индекс (если нужно)
6. Возврат подтверждения

### 7.2 Read Operations

```mermaid
graph LR
    A[Request] --> B[Router]
    B --> C[Service]
    C --> D[Repository]
    D --> E[(MongoDB)]
    E --> F[Index Lookup]
    F --> G[Data]
    G --> H[Transform]
    H --> I[Response]
```

**Пример: Загрузка истории**
1. Request с session_id
2. Repository запрос к MongoDB
3. MongoDB использует индекс `session_id + created_at`
4. Возврат отсортированных сообщений
5. Service форматирует
6. Response клиенту

---

## 8. FAISS Index Data Flow

### 8.1 Index Building (Startup)

```mermaid
sequenceDiagram
    participant APP as Application
    participant FS as FileSystem
    participant FAISS as FAISS Index
    
    APP->>FS: Найти embedding файлы
    FS-->>APP: [embeddings_batch_0.npy, ...]
    
    loop Для каждого batch
        APP->>FS: Загрузить .npy файл
        FS-->>APP: NumPy array
        APP->>APP: Объединить массивы
    end
    
    APP->>APP: Нормализовать векторы
    APP->>FAISS: Создать HNSW индекс
    APP->>FAISS: Добавить векторы
    FAISS-->>APP: Index ready
    APP->>APP: Сохранить в глобальные переменные
```

### 8.2 Search Flow

```mermaid
sequenceDiagram
    participant MS as MatchService
    participant YGPT as YandexGPT
    participant FAISS as FAISS Index
    participant MEM as Memory
    
    MS->>YGPT: embed_text(query)
    YGPT-->>MS: Query vector (256 dim)
    
    MS->>MS: Нормализовать вектор
    MS->>FAISS: search(query_vec, k=100)
    
    FAISS->>MEM: HNSW graph traversal
    MEM-->>FAISS: Distances & indices
    
    FAISS-->>MS: [idx1, idx2, ..., idx100]
    MS->>MS: Преобразовать в vacancy_ids
```

---

## 9. Error Flow

### 9.1 Error Handling Sequence

```mermaid
sequenceDiagram
    participant S as Service
    participant R as Router
    participant H as Handler
    participant U as User
    
    S->>S: Exception raised
    S-->>R: Raise exception
    R->>H: Global exception handler
    H->>H: Log error
    H->>H: Format error response
    H-->>R: JSONResponse(500, {detail: "..."})
    R-->>U: Error message
```

**Error Types:**
- **ConfigurationError:** При старте приложения
- **YandexGPTError:** При вызове API
- **MongoDBError:** При операциях с БД
- **FAISSError:** При поиске

---

## 10. Caching Strategy

### 10.1 Current State

**No Caching:**
- Все запросы к YandexGPT выполняются каждый раз
- Профили загружаются из БД при каждом запросе
- FAISS индекс загружается при старте (в памяти)

### 10.2 Future Improvements

**Potential Caching:**
- Кэширование LLM ответов для одинаковых запросов
- Кэширование профилей в памяти (TTL)
- Redis для распределенного кэша

---

**Document Status:** ✅ Complete



