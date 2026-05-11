@echo off
chcp 65001 >nul
setlocal

echo.
echo  EMAC - Gestion des migrations SQL
echo  ==================================
echo.

REM Verifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERREUR : Python n'est pas dans le PATH.
    pause
    exit /b 1
)

REM Verifier le .env
if not exist "%~dp0.env" (
    echo  ERREUR : fichier .env introuvable dans %~dp0
    echo  Creez-le a partir de config/.env.example
    pause
    exit /b 1
)

REM Gerer l'argument --dry-run
set DRY_RUN=
if /i "%1"=="--dry-run" set DRY_RUN=--dry-run

python scripts\smart_migrate.py %DRY_RUN%

echo.
pause
