@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo  Синхронизация с GitHub
echo ========================================
echo.

echo [1/4] Проверка статуса...
git status --short
echo.

echo [2/4] Добавление всех изменений...
git add -A
if errorlevel 1 (
    echo ОШИБКА: Не удалось добавить файлы
    pause
    exit /b 1
)
echo.

echo [3/4] Создание коммита...
git commit -m "Update: автоматическая синхронизация изменений"
if errorlevel 1 (
    echo Пропуск коммита (нет изменений или уже закоммичено)
) else (
    echo Коммит создан успешно
)
echo.

echo [4/4] Отправка в GitHub...
git push origin diploma-version
if errorlevel 1 (
    echo ОШИБКА: Не удалось отправить изменения
    echo Проверьте подключение к интернету и права доступа
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo  УСПЕШНО: Все изменения отправлены в GitHub!
    echo ========================================
)
echo.
pause

