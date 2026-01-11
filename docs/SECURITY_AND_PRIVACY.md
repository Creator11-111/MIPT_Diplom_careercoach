# Security and Privacy Documentation

**Date:** 2025-01-12  
**Version:** 1.0.0

---

## 1. Overview

Документ описывает меры безопасности и политику конфиденциальности системы Financial Career Coach.

---

## 2. Security Measures

### 2.1 Secrets Management

**Current Implementation:**
- Все секреты хранятся в переменных окружения
- Никакие секреты не хранятся в коде или репозитории
- Использование `.env` файлов для локальной разработки (не коммитятся)

**Secrets:**
- `YANDEX_API_KEY` - API ключ для YandexGPT
- `YANDEX_IAM_TOKEN` - IAM токен (альтернатива API ключу)
- `MONGO_URI` - URI подключения к MongoDB
- `YANDEX_FOLDER_ID` - ID папки в Yandex Cloud

**Best Practices:**
- ✅ Секреты в environment variables
- ✅ Валидация наличия секретов при старте
- ✅ Использование Google Secret Manager в production (рекомендуется)

**Future Improvements:**
- Интеграция с Google Secret Manager
- Ротация секретов
- Аудит доступа к секретам

---

### 2.2 API Security

**Rate Limiting:**
- **Лимит:** 100 запросов в минуту на IP-адрес
- **Window:** 60 секунд
- **Implementation:** Middleware на уровне FastAPI
- **Response:** `429 Too Many Requests` с заголовком `Retry-After`

**CORS:**
- Настраивается через переменную окружения `CORS_ORIGINS`
- По умолчанию: `*` (только для разработки)
- Production: Список разрешенных доменов

**Input Validation:**
- Все входные данные валидируются через Pydantic
- Максимальная длина сообщений: 5000 символов
- Валидация session_id, user_id формата

**Error Handling:**
- Не раскрываем внутренние детали ошибок пользователям
- Логирование ошибок для администраторов
- Graceful degradation при недоступности внешних сервисов

---

### 2.3 Data Security

**MongoDB:**
- Использование MongoDB Atlas (управляемый сервис)
- Подключение через SSL/TLS
- Индексы для быстрого поиска (безопасность через производительность)

**Data Encryption:**
- **In Transit:** HTTPS для всех HTTP запросов
- **At Rest:** MongoDB Atlas обеспечивает шифрование на уровне БД

**Data Access:**
- Текущая версия: Нет аутентификации (любой может получить доступ к любой сессии)
- **Future:** Добавление аутентификации и авторизации

---

### 2.4 External Services Security

**YandexGPT API:**
- Аутентификация через API ключ или IAM токен
- Все запросы через HTTPS
- Retry логика с экспоненциальной задержкой

**MongoDB Atlas:**
- IP whitelist (опционально)
- Database user с ограниченными правами
- Регулярные бэкапы

---

## 3. Privacy Policy

### 3.1 Data Collection

**Collected Data:**
- **Session Data:** ID сессии, user_id, состояние
- **Messages:** Все сообщения в диалоге (вопросы и ответы)
- **Profiles:** Структурированный профиль пользователя
- **Metadata:** Временные метки, типы сообщений

**Not Collected:**
- IP адреса (не сохраняются, только для rate limiting)
- Cookies (не используются)
- Личная информация, не указанная пользователем

### 3.2 Data Usage

**Purpose:**
- Предоставление услуг карьерного коучинга
- Подбор релевантных вакансий
- Построение карьерных планов
- Улучшение качества системы

**Third-Party Services:**
- **YandexGPT:** Обработка сообщений и генерация ответов
- **MongoDB Atlas:** Хранение данных
- **Google Cloud Run:** Хостинг приложения

### 3.3 Data Storage

**Location:**
- MongoDB Atlas (может быть в разных регионах)
- Google Cloud Run (регион: us-central1)

**Retention:**
- Данные хранятся до удаления пользователем
- Пользователь может удалить сессию и все связанные данные
- Нет автоматического удаления старых данных (в текущей версии)

### 3.4 Data Access

**User Access:**
- Пользователь может просматривать свои сессии через API
- Пользователь может удалить свои сессии
- Экспорт данных в PDF/Word

**Administrator Access:**
- Доступ к MongoDB для технической поддержки
- Логи для отладки (не содержат персональных данных)

**Third-Party Access:**
- YandexGPT получает сообщения для обработки (согласно их политике конфиденциальности)
- MongoDB Atlas (управляемый сервис, согласно их политике)

---

## 4. Compliance

### 4.1 GDPR (General Data Protection Regulation)

**Rights of Data Subjects:**
- ✅ **Right to Access:** Пользователь может получить свои данные через API
- ✅ **Right to Erasure:** Пользователь может удалить свои сессии
- ⚠️ **Right to Portability:** Экспорт в PDF/Word (частично)
- ❌ **Right to Rectification:** Нет возможности редактировать данные (только удаление и создание новой сессии)

**Data Minimization:**
- Собираем только необходимые данные для предоставления услуг
- Не собираем избыточную информацию

**Consent:**
- Использование системы подразумевает согласие на обработку данных
- Явное согласие не запрашивается (упрощенная версия)

### 4.2 Russian Data Protection Law (152-ФЗ)

**Requirements:**
- Хранение данных на территории РФ (если требуется)
- Обработка персональных данных с согласия субъекта
- Защита персональных данных от несанкционированного доступа

**Current Status:**
- ⚠️ Данные могут храниться вне РФ (MongoDB Atlas, Google Cloud)
- ⚠️ Нет явного запроса согласия
- ✅ Защита данных через HTTPS и безопасные подключения

---

## 5. Security Best Practices

### 5.1 Code Security

**Dependencies:**
- Регулярное обновление зависимостей
- Проверка уязвимостей (future: автоматическое сканирование)

**Input Sanitization:**
- Валидация всех входных данных
- Защита от SQL injection (не применимо, используется MongoDB)
- Защита от XSS (на уровне фронтенда)

**Error Handling:**
- Не раскрываем внутренние детали в ошибках
- Логирование для администраторов
- Graceful degradation

### 5.2 Infrastructure Security

**Deployment:**
- Docker контейнеры для изоляции
- Минимальные привилегии
- Регулярные обновления базового образа

**Monitoring:**
- Логирование всех запросов
- Мониторинг ошибок
- Алерты при критических ошибках (future)

**Backup:**
- MongoDB Atlas автоматические бэкапы
- Резервное копирование эмбеддингов (future)

---

## 6. Known Security Limitations

### 6.1 Current Limitations

**No Authentication:**
- Любой может получить доступ к любой сессии, зная session_id
- Нет защиты от несанкционированного доступа

**No Authorization:**
- Нет разграничения прав доступа
- Все пользователи имеют одинаковые права

**No Encryption at Application Level:**
- Данные не шифруются на уровне приложения
- Полагаемся на шифрование MongoDB Atlas и HTTPS

**Rate Limiting by IP:**
- Может быть обойден через VPN или прокси
- Нет защиты от распределенных атак

### 6.2 Future Improvements

**Authentication:**
- Добавление системы аутентификации (OAuth, JWT)
- Защита сессий через токены

**Authorization:**
- Разграничение прав доступа
- Роли пользователей (user, admin)

**Enhanced Security:**
- WAF (Web Application Firewall)
- DDoS защита
- Интеграция с Google Cloud Security

---

## 7. Incident Response

### 7.1 Security Incidents

**Types:**
- Утечка данных
- Несанкционированный доступ
- DDoS атака
- Компрометация секретов

**Response Procedure:**
1. Обнаружение инцидента
2. Изоляция затронутых систем
3. Оценка масштаба
4. Устранение уязвимости
5. Уведомление пользователей (если требуется)
6. Пост-мортем анализ

### 7.2 Data Breach

**Notification:**
- Уведомление пользователей в течение 72 часов (GDPR)
- Уведомление регуляторов (если требуется)

**Mitigation:**
- Отзыв скомпрометированных токенов
- Сброс паролей (когда будет аутентификация)
- Усиление мер безопасности

---

## 8. Privacy by Design

### 8.1 Principles

**Minimal Data Collection:**
- Собираем только необходимые данные
- Не храним избыточную информацию

**Data Purpose Limitation:**
- Данные используются только для заявленных целей
- Не передаем данные третьим лицам без необходимости

**User Control:**
- Пользователь может удалить свои данные
- Пользователь может экспортировать свои данные

**Transparency:**
- Документированная политика конфиденциальности
- Понятные пользователю сообщения

---

## 9. Recommendations for Production

### 9.1 Immediate Actions

1. **Add Authentication:**
   - Реализовать систему аутентификации
   - Защитить сессии через токены

2. **Restrict CORS:**
   - Указать конкретные разрешенные домены
   - Убрать `*` для production

3. **Use Secret Manager:**
   - Интегрировать Google Secret Manager
   - Убрать секреты из environment variables где возможно

4. **Enable Logging:**
   - Структурированное логирование
   - Мониторинг и алерты

### 9.2 Long-term Improvements

1. **Data Encryption:**
   - Шифрование на уровне приложения
   - Key management через Google Cloud KMS

2. **Access Control:**
   - RBAC (Role-Based Access Control)
   - Аудит доступа к данным

3. **Compliance:**
   - Полное соответствие GDPR
   - Соответствие 152-ФЗ (если требуется)

4. **Security Testing:**
   - Регулярные penetration тесты
   - Автоматическое сканирование уязвимостей

---

## 10. Contact

**Security Issues:**
- Сообщить о проблемах безопасности через GitHub Issues (private)
- Или напрямую разработчикам

**Privacy Questions:**
- Вопросы о конфиденциальности: см. документацию
- Запросы на удаление данных: через API или контакт разработчиков

---

**Document Status:** ✅ Complete



