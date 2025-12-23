@echo off
REM ========================================
REM Script de déploiement EMAC sur réseau
REM ========================================

setlocal enabledelayedexpansion

cls
echo.
echo ================================================
echo   DEPLOIEMENT EMAC SUR PARTAGE RESEAU
echo ================================================
echo.

REM Configuration
set "SOURCE=%~dp0..\App\dist\EMAC"
set "DESTINATION=\\s_data\Bureautique\Services\THOMAS\EMAC"
set "LOG_FILE=%~dp0deploiement.log"

echo Date : %date% %time% > "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM 1. Vérifier que la source existe
echo [1/4] Verification de la source...
echo.

if not exist "%SOURCE%\EMAC.exe" (
    echo    [ERREUR] Source introuvable : %SOURCE%
    echo    Compilez d'abord l'application avec : build_optimized.bat
    echo.
    echo ERREUR: Source introuvable >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo    [OK] Source trouvee : %SOURCE%
echo    Source : %SOURCE% >> "%LOG_FILE%"
echo.

REM Vérifier taille
for /f %%A in ('dir /s /a "%SOURCE%" ^| find "octets"') do set "SIZE_INFO=%%A"
echo    Taille a copier : ~182 Mo
echo.

REM 2. Vérifier que la destination est accessible
echo [2/4] Verification du partage reseau...
echo.

REM Tester l'accès au partage
net use | findstr "\\\\s_data" >nul 2>&1
if errorlevel 1 (
    echo    Tentative de connexion au partage...
)

REM Créer le dossier destination s'il n'existe pas
if not exist "%DESTINATION%" (
    echo    Creation du dossier : %DESTINATION%
    mkdir "%DESTINATION%" 2>nul
    if errorlevel 1 (
        echo.
        echo    [ERREUR] Impossible de creer le dossier sur le reseau
        echo    Verifiez :
        echo    - Que vous etes connecte au reseau de l'entreprise
        echo    - Que vous avez les droits d'ecriture sur \\s_data
        echo    - Que le chemin est correct
        echo.
        echo ERREUR: Destination inaccessible >> "%LOG_FILE%"
        pause
        exit /b 1
    )
)

echo    [OK] Destination accessible : %DESTINATION%
echo    Destination : %DESTINATION% >> "%LOG_FILE%"
echo.

REM 3. Copier avec robocopy
echo [3/4] Copie des fichiers sur le reseau...
echo.
echo    Cette operation peut prendre 2-5 minutes selon la vitesse reseau
echo    Progression affichee ci-dessous :
echo.
echo ------------------------------------------------

echo Debut copie : %time% >> "%LOG_FILE%"

robocopy "%SOURCE%" "%DESTINATION%" /MIR /R:2 /W:5 /NP /LOG+:"%LOG_FILE%"

set "RC_EXIT=%errorlevel%"

echo Fin copie : %time% >> "%LOG_FILE%"
echo Exit code : %RC_EXIT% >> "%LOG_FILE%"

echo ------------------------------------------------
echo.

REM Robocopy return codes: 0-7 = success, 8+ = error
if %RC_EXIT% GEQ 8 (
    echo.
    echo    [ERREUR] Echec de la copie (code %RC_EXIT%)
    echo    Consultez le log : %LOG_FILE%
    echo.
    echo ERREUR: Copie failed >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo    [OK] Copie terminee avec succes
echo.

REM 4. Vérifier le résultat
echo [4/4] Verification du deploiement...
echo.

if exist "%DESTINATION%\EMAC.exe" (
    echo    [OK] EMAC.exe present sur le reseau
) else (
    echo    [ERREUR] EMAC.exe manquant !
    pause
    exit /b 1
)

if exist "%DESTINATION%\.env" (
    echo    [OK] .env present
) else (
    echo    [ATTENTION] .env manquant - l'application ne pourra pas se connecter a la BDD
)

if exist "%DESTINATION%\_internal" (
    echo    [OK] Dossier _internal present
) else (
    echo    [ERREUR] _internal manquant !
    pause
    exit /b 1
)

echo.
echo ================================================
echo   DEPLOIEMENT TERMINE AVEC SUCCES
echo ================================================
echo.
echo   Emplacement : %DESTINATION%
echo   Fichiers deployes :
echo   - EMAC.exe
echo   - .env
echo   - _internal\ (complet)
echo.
echo ================================================
echo   PROCHAINES ETAPES
echo ================================================
echo.
echo 1. Configurez Lancer_EMAC.bat (ligne 12) :
echo    set "SOURCE_RESEAU=%DESTINATION%"
echo.
echo 2. Distribuez Lancer_EMAC.bat aux utilisateurs
echo.
echo 3. Les utilisateurs double-cliqueront sur Lancer_EMAC.bat
echo    (pas sur EMAC.exe directement)
echo.
echo ================================================
echo.
echo Log complet : %LOG_FILE%
echo.
pause
exit /b 0
