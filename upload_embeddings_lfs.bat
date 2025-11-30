@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo  Загрузка эмбеддингов в GitHub через Git LFS
echo ========================================
echo.

echo [1/6] Проверка Git LFS...
git lfs version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Git LFS не установлен!
    echo Установите с https://git-lfs.github.com/
    pause
    exit /b 1
)
echo OK - Git LFS установлен
echo.

echo [2/6] Инициализация Git LFS в репозитории...
git lfs install --force
if errorlevel 1 (
    echo ВНИМАНИЕ: Git LFS уже инициализирован или ошибка
)
echo.

echo [3/6] Проверка .gitattributes...
if not exist ".gitattributes" (
    echo Создание .gitattributes...
    echo data/embeddings/**/*.npy filter=lfs diff=lfs merge=lfs -text > .gitattributes
    git add .gitattributes
    git commit -m "Add Git LFS tracking for embeddings"
) else (
    echo .gitattributes уже существует
    git add .gitattributes
)
echo.

echo [4/6] Добавление эмбеддингов в Git LFS...
echo ВНИМАНИЕ: Это может занять время (2574 файла)...
echo Пожалуйста, подождите...
git add -A data/embeddings/
if errorlevel 1 (
    echo ОШИБКА: Не удалось добавить эмбеддинги
    echo Проверьте, что папка data/embeddings/ существует
    pause
    exit /b 1
)
echo OK - Эмбеддинги добавлены в Git LFS
echo.
echo Проверка статуса добавленных файлов...
git status --short data/embeddings/ | find /c /v "" > temp_count.txt
set /p COUNT=<temp_count.txt
del temp_count.txt
echo Найдено файлов для коммита: %COUNT%
echo.

echo [5/6] Создание коммита...
echo Проверка, есть ли изменения для коммита...
git diff --cached --quiet
if errorlevel 1 (
    echo Есть изменения, создаю коммит...
    git commit -m "Add embeddings via Git LFS (2574 files)"
    if errorlevel 1 (
        echo ОШИБКА: Не удалось создать коммит
        pause
        exit /b 1
    )
    echo OK - Коммит создан
) else (
    echo ВНИМАНИЕ: Нет изменений для коммита
    echo Проверяю, может быть эмбеддинги уже закоммичены...
    git log --oneline -5 --all -- data/embeddings/ | find "embeddings" >nul
    if errorlevel 1 (
        echo Эмбеддинги не найдены в истории коммитов
        echo Попробую добавить их заново...
        git add -f data/embeddings/
        git commit -m "Add embeddings via Git LFS (2574 files)"
        if errorlevel 1 (
            echo ОШИБКА: Не удалось создать коммит
            pause
            exit /b 1
        )
        echo OK - Коммит создан
    ) else (
        echo Эмбеддинги уже закоммичены ранее
    )
)
echo.

echo [6/6] Отправка в GitHub...
echo ВНИМАНИЕ: Загрузка может занять 10-30 минут!
echo Не прерывайте процесс!
echo.
git push origin diploma-version
if errorlevel 1 (
    echo.
    echo ОШИБКА: Не удалось отправить изменения
    echo Возможные причины:
    echo - Проблемы с интернет-соединением
    echo - Недостаточно места в GitHub LFS (нужен платный план для больших файлов)
    echo - Проблемы с аутентификацией
    echo.
    echo Попробуйте выполнить вручную:
    echo   git push origin diploma-version
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo  УСПЕШНО! Эмбеддинги загружены в GitHub
    echo ========================================
    echo.
    echo Теперь на Railway эмбеддинги будут автоматически загружаться
    echo при деплое из GitHub!
)
echo.
pause

