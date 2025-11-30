@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo  Настройка Git LFS для эмбеддингов
echo ========================================
echo.
echo [1/5] Инициализация Git LFS...
git lfs install
if errorlevel 1 (
    echo ОШИБКА: Git LFS не установлен!
    echo Установите с https://git-lfs.github.com/
    pause
    exit /b 1
)
echo OK
echo.
echo [2/5] Добавление .gitattributes и .gitignore...
git add .gitattributes .gitignore
if errorlevel 1 (
    echo ОШИБКА: Не удалось добавить файлы
    pause
    exit /b 1
)
echo OK
echo.
echo [3/5] Коммит .gitattributes...
git commit -m "Add Git LFS tracking for embeddings"
if errorlevel 1 (
    echo ВНИМАНИЕ: Коммит не создан (возможно, нет изменений)
) else (
    echo OK
)
echo.
echo [4/5] Добавление эмбеддингов...
echo ВНИМАНИЕ: Это может занять время (2574 файла)...
echo Пожалуйста, подождите...
git add data/embeddings/
if errorlevel 1 (
    echo ОШИБКА: Не удалось добавить эмбеддинги
    pause
    exit /b 1
)
echo OK
echo.
echo [5/5] Коммит эмбеддингов...
git commit -m "Add embeddings via Git LFS"
if errorlevel 1 (
    echo ВНИМАНИЕ: Коммит не создан (возможно, нет изменений)
) else (
    echo OK
)
echo.
echo ========================================
echo  ГОТОВО!
echo ========================================
echo.
echo Теперь выполните команду для отправки в GitHub:
echo   git push origin diploma-version
echo.
echo ВНИМАНИЕ: Загрузка может занять 10-30 минут!
echo Не прерывайте процесс!
echo.
pause



