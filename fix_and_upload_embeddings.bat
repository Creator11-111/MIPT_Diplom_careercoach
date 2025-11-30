@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo  Исправление и загрузка эмбеддингов
echo ========================================
echo.

echo [1/7] Исправление конфликта Git LFS hook...
git lfs update --force
echo OK
echo.

echo [2/7] Инициализация Git LFS...
git lfs install --force
echo OK
echo.

echo [3/7] Добавление всех файлов (включая эмбеддинги)...
git add -A
echo OK
echo.

echo [4/7] Проверка статуса...
git status --short | find /c /v "" > temp_count.txt
set /p FILE_COUNT=<temp_count.txt
del temp_count.txt
echo Найдено измененных файлов: %FILE_COUNT%
echo.

echo [5/7] Проверка эмбеддингов в Git LFS...
git lfs ls-files > temp_lfs_files.txt 2>nul
if exist temp_lfs_files.txt (
    find /c /v "" temp_lfs_files.txt > temp_lfs_count.txt
    set /p LFS_COUNT=<temp_lfs_count.txt
    del temp_lfs_count.txt
    del temp_lfs_files.txt
    echo Файлов в Git LFS: %LFS_COUNT%
) else (
    echo Файлов в Git LFS: 0 (еще не добавлены)
)
echo.

echo [6/7] Создание коммита...
git diff --cached --quiet
if errorlevel 1 (
    echo Есть изменения, создаю коммит...
    git commit -m "Add embeddings via Git LFS and update configuration"
    if errorlevel 1 (
        echo ОШИБКА: Не удалось создать коммит
        echo Показываю статус...
        git status
        pause
        exit /b 1
    )
    echo OK - Коммит создан
) else (
    echo Нет изменений для коммита
    echo Проверяю последние коммиты...
    git log --oneline -3
)
echo.

echo [7/7] Отправка в GitHub...
echo ВНИМАНИЕ: Загрузка может занять 10-30 минут!
echo Не прерывайте процесс!
echo.
git push origin diploma-version
if errorlevel 1 (
    echo.
    echo ОШИБКА: Не удалось отправить изменения
    echo.
    echo Попробуйте выполнить вручную:
    echo   git push origin diploma-version
    echo.
    echo Или проверьте:
    echo - Подключение к интернету
    echo - Лимиты GitHub LFS (бесплатный план: 1 GB)
    echo - Аутентификацию GitHub
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

