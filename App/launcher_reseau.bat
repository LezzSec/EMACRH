@echo off
REM ========================================
REM Lanceur EMAC pour réseau partagé
REM Copie l'exe localement pour démarrage rapide
REM ========================================

setlocal enabledelayedexpansion

REM Configuration
set "SOURCE_RESEAU=\\chemin\vers\partage\EMAC"
set "CACHE_LOCAL=%LOCALAPPDATA%\EMAC_Cache"
set "VERSION_FILE=version.txt"

echo.
echo ================================================
echo   LANCEMENT EMAC (depuis réseau)
echo ================================================
echo.

REM 1. Créer le dossier cache local s'il n'existe pas
if not exist "%CACHE_LOCAL%" (
    echo [1/3] Création du cache local...
    mkdir "%CACHE_LOCAL%"
)

REM 2. Vérifier si mise à jour nécessaire
set "NEED_COPY=0"

if not exist "%CACHE_LOCAL%\EMAC.exe" (
    echo [2/3] Première installation locale...
    set "NEED_COPY=1"
) else (
    REM Comparer les dates de modification
    for %%A in ("%SOURCE_RESEAU%\EMAC.exe") do set "DATE_RESEAU=%%~tA"
    for %%B in ("%CACHE_LOCAL%\EMAC.exe") do set "DATE_LOCAL=%%~tB"

    if not "!DATE_RESEAU!"=="!DATE_LOCAL!" (
        echo [2/3] Mise à jour détectée...
        set "NEED_COPY=1"
    ) else (
        echo [2/3] Version locale à jour.
    )
)

REM 3. Copier si nécessaire
if "%NEED_COPY%"=="1" (
    echo Copie depuis le réseau... (peut prendre 30-60 secondes)
    robocopy "%SOURCE_RESEAU%" "%CACHE_LOCAL%" /MIR /NFL /NDL /NJH /NJS /nc /ns /np

    if errorlevel 8 (
        echo.
        echo ❌ ERREUR : Échec de la copie depuis le réseau
        echo    Vérifiez que le partage est accessible : %SOURCE_RESEAU%
        pause
        exit /b 1
    )
)

REM 4. Lancer depuis le cache local
echo [3/3] Lancement de l'application...
echo.
cd /d "%CACHE_LOCAL%"
start "" "%CACHE_LOCAL%\EMAC.exe"

echo ✅ Application lancée
echo.
timeout /t 2 /nobreak >nul
exit /b 0
