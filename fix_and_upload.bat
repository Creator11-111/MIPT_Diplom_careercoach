@echo off
chcp 65001 >nul
echo ========================================
echo  Исправление и загрузка в GitHub
echo ========================================
echo.

cd /d "%~dp0"

echo [1/6] Создание новой ветки без истории...
git checkout --orphan new-branch
if errorlevel 1 (
    echo ОШИБКА: Не удалось создать новую ветку
    pause
    exit /b 1
)
echo OK
echo.

echo [2/6] Добавление всех файлов (большой файл исключен через .gitignore)...
git add .
if errorlevel 1 (
    echo ОШИБКА: Не удалось добавить файлы
    pause
    exit /b 1
)
echo OK
echo.

echo [3/6] Создание первого коммита...
git commit -m "Initial commit: Financial Career Coach (without large files)"
if errorlevel 1 (
    echo ОШИБКА: Не удалось создать коммит
    pause
    exit /b 1
)
echo OK
echo.

echo [4/6] Удаление старой ветки...
git branch -D diploma-version
echo OK (ветка может не существовать, это нормально)
echo.

echo [5/6] Переименование новой ветки...
git branch -M diploma-version
if errorlevel 1 (
    echo ОШИБКА: Не удалось переименовать ветку
    pause
    exit /b 1
)
echo OK
echo.

echo [6/6] Принудительная загрузка в GitHub...
echo ВНИМАНИЕ: Это перезапишет ветку diploma-version в GitHub!
echo.
git push -f origin diploma-version
if errorlevel 1 (
    echo.
    echo ОШИБКА: Не удалось загрузить в GitHub
    echo Проверьте подключение к интернету и учетные данные GitHub
    pause
    exit /b 1
)

echo.
echo ========================================
echo  УСПЕШНО! Проект загружен в GitHub
echo ========================================
echo.
echo Проверьте: https://github.com/Creator11-111/MIPT_Diplom_careercoach
echo.
pause

