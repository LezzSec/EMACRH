@echo off
REM ========================================
REM EMAC - Lanceur Local (Developpement)
REM Version 1.0
REM ========================================

setlocal enabledelayedexpansion

cls
echo.
echo ================================================
echo   EMAC - Lanceur Local (Developpement)
echo ================================================
echo.

REM Configuration pour developpement local
set "SOURCE=%~dp0..\App\dist\EMAC"
set "CACHE_LOCAL=%LOCALAPPDATA%\EMAC_Cache"
set "LOG_FILE=%CACHE_LOCAL%\launcher_local.log"

REM Creer le dossier de cache
if not exist "%CACHE_LOCAL%" mkdir "%CACHE_LOCAL%"

echo. > "%LOG_FILE%"
echo Lanceur Local EMAC - %date% %time% >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM 1. Verifier que la source existe
echo [1/3] Verification de la source...
echo Source : %SOURCE% >> "%LOG_FILE%"

if not exist "%SOURCE%\EMAC.exe" (
    echo.
    echo ❌ ERREUR : EMAC.exe introuvable
    echo    Chemin : %SOURCE%
    echo.
    echo ERREUR: EMAC.exe introuvable dans %SOURCE% >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo    ✅ Source trouvee : %SOURCE%
echo Source OK >> "%LOG_FILE%"
echo.

REM 2. Determiner si copie necessaire
set "NEED_COPY=0"

if not exist "%CACHE_LOCAL%\EMAC.exe" (
    set "NEED_COPY=1"
    echo [2/3] Premiere installation...
    echo Premiere installation detectee >> "%LOG_FILE%"
) else (
    REM Comparer les tailles
    for %%A in ("%SOURCE%\EMAC.exe") do set "SIZE_SOURCE=%%~zA"
    for %%B in ("%CACHE_LOCAL%\EMAC.exe") do set "SIZE_CACHE=%%~zB"

    if not "!SIZE_SOURCE!"=="!SIZE_CACHE!" (
        set "NEED_COPY=1"
        echo [2/3] Mise a jour detectee...
        echo Mise a jour detectee (taille differente) >> "%LOG_FILE%"
    ) else (
        echo [2/3] Cache local a jour
        echo Cache a jour >> "%LOG_FILE%"
    )
)
echo.

REM 3. Copier si necessaire
if "%NEED_COPY%"=="1" (
    echo    📂 Copie vers le cache local...
    echo    (Peut prendre 10-30 secondes)
    echo.
    echo Debut copie : %time% >> "%LOG_FILE%"

    REM Utiliser robocopy
    robocopy "%SOURCE%" "%CACHE_LOCAL%" /MIR /R:2 /W:2 /NFL /NDL /NJH /NJS /NP >> "%LOG_FILE%" 2>&1

    set "RC_EXIT=%errorlevel%"
    echo Robocopy exit code: !RC_EXIT! >> "%LOG_FILE%"

    if !RC_EXIT! GEQ 8 (
        echo.
        echo ❌ ERREUR : Echec de la copie
        echo    Consultez : %LOG_FILE%
        echo.
        echo ERREUR: Robocopy failed >> "%LOG_FILE%"
        pause
        exit /b 1
    )

    echo Fin copie : %time% >> "%LOG_FILE%"
    echo    ✅ Copie terminee
    echo.
)

REM 4. Verifier que .env existe
if not exist "%CACHE_LOCAL%\.env" (
    echo ⚠️  ATTENTION : .env manquant dans le cache
    echo    Copie depuis la source...
    copy /y "%SOURCE%\.env" "%CACHE_LOCAL%\.env" >nul 2>&1
    if errorlevel 1 (
        echo    ❌ Impossible de copier .env
        echo ERREUR: .env copy failed >> "%LOG_FILE%"
    ) else (
        echo    ✅ .env copie
    )
    echo.
)

REM 5. Lancer l'application
echo [3/3] Lancement d'EMAC...
echo.
echo Lancement : %time% >> "%LOG_FILE%"
echo Commande : "%CACHE_LOCAL%\EMAC.exe" >> "%LOG_FILE%"

cd /d "%CACHE_LOCAL%"
start "" "%CACHE_LOCAL%\EMAC.exe"

if errorlevel 1 (
    echo.
    echo ❌ ERREUR : Impossible de lancer l'application
    echo    Consultez : %LOG_FILE%
    echo.
    echo ERREUR: Failed to start EMAC.exe >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo ✅ Application lancee
echo Application started successfully >> "%LOG_FILE%"
echo.
echo Cache local : %CACHE_LOCAL%
echo Log file : %LOG_FILE%
echo.

REM Attendre 2 secondes puis fermer
timeout /t 2 /nobreak >nul
exit /b 0
