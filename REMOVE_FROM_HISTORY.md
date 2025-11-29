# 🔧 Удаление большого файла из истории Git

## Проблема
Файл `data/financial_vacancies.parquet` уже был закоммичен в истории Git, и GitHub проверяет всю историю, а не только последний коммит.

## Решение: Удалить файл из всей истории

Выполните эти команды в PowerShell:

```powershell
# 1. Удалите файл из всей истории Git
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch data/financial_vacancies.parquet" --prune-empty --tag-name-filter cat -- --all

# 2. Принудительно обновите удаленный репозиторий
git push origin --force --all

# 3. Очистите резервные копии
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

## Альтернативный способ (если filter-branch не работает)

Если команда выше не работает, используйте более простой способ:

```powershell
# 1. Создайте новую ветку без истории
git checkout --orphan new-master

# 2. Добавьте все файлы (кроме большого)
git add .

# 3. Создайте первый коммит
git commit -m "Initial commit: Financial Career Coach (without large files)"

# 4. Удалите старую ветку
git branch -D diploma-version

# 5. Переименуйте новую ветку
git branch -M diploma-version

# 6. Принудительно загрузите в GitHub
git push -f origin diploma-version
```

## Важно!

После удаления файла из истории:
- Файл останется на вашем локальном диске
- Он не будет в GitHub
- При клонировании репозитория файла не будет
- Нужно будет сгенерировать его заново через `data_parsing/scrape_financial_vacancies_hh.py`

