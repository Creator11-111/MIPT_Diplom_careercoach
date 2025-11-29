# 🔧 Исправление: Файл слишком большой для GitHub

## Проблема
Файл `data/financial_vacancies.parquet` весит 201.77 MB, а GitHub ограничивает размер файлов до 100 MB.

## Решение

Выполните эти команды в PowerShell:

```powershell
# 1. Удалите большой файл из Git индекса (файл останется на диске)
git rm --cached data/financial_vacancies.parquet

# 2. Добавьте изменения в .gitignore (уже обновлен)
git add .gitignore

# 3. Создайте коммит без большого файла
git commit -m "Remove large parquet file from Git (use local data instead)"

# 4. Загрузите в GitHub
git push origin diploma-version
```

## Почему это нормально?

Файл `financial_vacancies.parquet` - это данные, которые:
- Можно сгенерировать заново через скрипт `data_parsing/scrape_financial_vacancies_hh.py`
- Не нужны в репозитории для работы кода
- Хранятся локально и загружаются в MongoDB при первом запуске

В `.gitignore` уже добавлено правило `data/*.parquet`, чтобы такие файлы не попадали в Git.

