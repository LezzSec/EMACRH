@echo off
REM ===================================================
REM Test de lancement EMAC avec capture d'erreurs
REM ===================================================

setlocal enabledelayedexpansion

cls
echo.
echo ================================================
echo   TEST DE LANCEMENT EMAC
echo ================================================
echo.

set "EXE_PATH=%~dp0..\App\dist\EMAC\EMAC.exe"
set "LOG_FILE=%~dp0test_lancement.log"

echo Test de lancement : %date% %time% > "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM Verifier que l'exe existe
if not exist "%EXE_PATH%" (
    echo ❌ ERREUR : EMAC.exe introuvable
    echo    Chemin : %EXE_PATH%
    echo.
    echo ERREUR: EMAC.exe introuvable >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo ✅ EMAC.exe trouvé : %EXE_PATH%
echo.

REM Verifier que .env existe
set "ENV_PATH=%~dp0..\App\dist\EMAC\.env"
if not exist "%ENV_PATH%" (
    echo ⚠️  ATTENTION : .env introuvable
    echo    L'application risque de crasher
    echo.
    echo WARNING: .env missing >> "%LOG_FILE%"
) else (
    echo ✅ .env trouvé
    echo.
)

REM Lancer EMAC et capturer la sortie
echo Lancement d'EMAC en mode console...
echo (La fenêtre restera ouverte pour voir les erreurs)
echo.
echo Chemin exe : %EXE_PATH% >> "%LOG_FILE%"
echo Lancement : %time% >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM Aller dans le dossier de l'exe
cd /d "%~dp0..\App\dist\EMAC"

REM Lancer l'exe SANS start (pour voir les erreurs dans la console)
echo Execution de EMAC.exe... >> "%LOG_FILE%"
"%EXE_PATH%" >> "%LOG_FILE%" 2>&1

set "EXIT_CODE=%errorlevel%"

echo. >> "%LOG_FILE%"
echo Fin : %time% >> "%LOG_FILE%"
echo Code de sortie : %EXIT_CODE% >> "%LOG_FILE%"

if %EXIT_CODE% NEQ 0 (
    echo.
    echo.
    echo ❌ L'application s'est terminée avec le code : %EXIT_CODE%
    echo.
    echo Consultez le log : %LOG_FILE%
    echo.
) else (
    echo.
    echo ✅ L'application s'est fermée normalement
    echo.
)

pause
exit /b %EXIT_CODE%
