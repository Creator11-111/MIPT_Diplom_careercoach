@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo  Проверка статуса эмбеддингов
echo ========================================
echo.

echo [1/4] Проверка Git статуса...
git status --short
echo.

echo [2/4] Проверка последних коммитов...
git log --oneline -5
echo.

echo [3/4] Проверка файлов в Git LFS...
git lfs ls-files | find /c /v "" > temp_lfs.txt 2>nul
if exist temp_lfs.txt (
    set /p LFS_COUNT=<temp_lfs.txt
    del temp_lfs.txt
    echo Файлов отслеживается через Git LFS: %LFS_COUNT%
    if %LFS_COUNT% GTR 0 (
        echo Первые 10 файлов:
        git lfs ls-files | head -n 10
    )
) else (
    echo Файлов в Git LFS: 0
)
echo.

echo [4/4] Проверка связи с GitHub...
git remote -v
echo.
git ls-remote --heads origin diploma-version >nul 2>&1
if errorlevel 1 (
    echo ВНИМАНИЕ: Не удалось подключиться к GitHub
    echo Проверьте интернет-соединение
) else (
    echo Связь с GitHub: OK
    echo.
    echo Проверка, отправлены ли изменения...
    git status -sb
)
echo.
echo ========================================
echo  Результат проверки
echo ========================================
echo.
pause

