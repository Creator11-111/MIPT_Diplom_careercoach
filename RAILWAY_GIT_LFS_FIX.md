# Исправление проблемы с Git LFS на Railway

## Проблема

Railway не может установить Git LFS в контейнере, потому что он не включен в базовый образ Nixpacks.

## Решение

Создан файл `nixpacks.toml`, который:
1. Устанавливает `git-lfs` через Nixpacks в фазе `setup`
2. Инициализирует Git LFS в фазе `build`
3. Загружает эмбеддинги через `git lfs pull`

## Что было сделано

1. ✅ Создан `nixpacks.toml` с конфигурацией для установки Git LFS
2. ✅ Обновлен `railway.json` (убран buildCommand, так как теперь это в nixpacks.toml)

## Следующие шаги

1. **Закоммитьте изменения:**
   ```bash
   git add nixpacks.toml railway.json
   git commit -m "Add Git LFS support for Railway deployment"
   git push origin diploma-version
   ```

2. **Railway автоматически задеплоит** с новой конфигурацией

3. **Проверьте логи Railway** после деплоя:
   - Должны увидеть: `git lfs install` и `git lfs pull`
   - Должны увидеть: `✅ FAISS индекс построен: X вакансий`

## Если проблема сохраняется

Если Git LFS все еще не работает, можно использовать альтернативный подход:

1. **Генерировать эмбеддинги на Railway при первом запуске**
2. **Использовать внешнее хранилище** (S3, Google Cloud Storage)

Но сначала попробуйте с `nixpacks.toml` - это должно решить проблему.

