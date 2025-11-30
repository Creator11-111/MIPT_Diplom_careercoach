@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo  Деплой на Railway с локального компьютера
echo ========================================
echo.

echo [1/5] Проверка Railway CLI...
railway --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Railway CLI не установлен!
    echo.
    echo Установите Railway CLI:
    echo   1. Через npm: npm install -g @railway/cli
    echo   2. Или через PowerShell: iwr https://railway.app/install.ps1 ^| iex
    echo   3. Или через Scoop: scoop install railway
    echo.
    pause
    exit /b 1
)
echo OK - Railway CLI установлен
echo.

echo [2/5] Проверка авторизации...
railway whoami >nul 2>&1
if errorlevel 1 (
    echo ВНИМАНИЕ: Вы не авторизованы в Railway
    echo Выполняю авторизацию...
    railway login
    if errorlevel 1 (
        echo ОШИБКА: Не удалось авторизоваться
        pause
        exit /b 1
    )
) else (
    echo OK - Авторизованы в Railway
)
echo.

echo [3/5] Проверка инициализации проекта...
if not exist ".railway" (
    echo Проект не инициализирован, инициализирую...
    railway init
    if errorlevel 1 (
        echo ОШИБКА: Не удалось инициализировать проект
        pause
        exit /b 1
    )
) else (
    echo OK - Проект инициализирован
)
echo.

echo [4/5] Проверка переменных окружения...
echo Убедитесь, что в Railway настроены переменные:
echo   - MONGO_URI
echo   - MONGO_DB
echo   - YANDEX_FOLDER_ID
echo   - YANDEX_API_KEY
echo   - APP_ENV
echo.
echo Для настройки: railway variables
echo.
pause
echo.

echo [5/5] Деплой на Railway...
echo ВНИМАНИЕ: Это может занять несколько минут!
echo Не прерывайте процесс!
echo.
railway up
if errorlevel 1 (
    echo.
    echo ОШИБКА: Не удалось задеплоить
    echo Проверьте логи: railway logs
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo  УСПЕШНО! Деплой завершен
    echo ========================================
    echo.
    echo Полезные команды:
    echo   railway logs    - просмотр логов
    echo   railway open    - открыть сайт
    echo   railway status - статус деплоя
    echo.
)
echo.
pause

