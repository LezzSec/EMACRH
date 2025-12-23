@echo off
REM ===================================================
REM Diagnostic de lenteur EMAC - Version simple
REM ===================================================

setlocal enabledelayedexpansion

REM Creer le fichier de rapport
set "RAPPORT=%~dp0diagnostic_rapport.txt"

echo Demarrage du diagnostic...
echo Le rapport sera dans : %RAPPORT%
echo.

REM Appeler le script principal et capturer toute la sortie
call :DIAGNOSTIC > "%RAPPORT%" 2>&1

REM Afficher le rapport
type "%RAPPORT%"

echo.
echo.
echo ===================================================
echo   RAPPORT SAUVEGARDE DANS :
echo   %RAPPORT%
echo ===================================================
echo.
echo Vous pouvez ouvrir ce fichier avec Notepad
echo.
pause

REM Ouvrir le fichier automatiquement
notepad "%RAPPORT%"
exit /b 0

REM ===================================================
REM Fonction de diagnostic
REM ===================================================
:DIAGNOSTIC

echo ===================================================
echo   DIAGNOSTIC DE LENTEUR EMAC
echo   Date : %date% %time%
echo ===================================================
echo.

REM 1. Emplacement de l'exe
echo [1/6] Emplacement d'execution
echo --------------------------------

set "EXE_PATH=%~dp0..\App\dist\EMAC\EMAC.exe"
if exist "%EXE_PATH%" (
    for %%I in ("%EXE_PATH%") do set "EXE_FULL=%%~fI"
    echo Chemin : !EXE_FULL!

    echo !EXE_FULL! | findstr /C:"\\\\" >nul
    if !errorlevel! EQU 0 (
        echo Statut : [PROBLEME] EXE SUR PARTAGE RESEAU
        echo Impact : Demarrage 2-5 minutes
        echo Solution : Utiliser Lancer_EMAC.bat
    ) else (
        echo Statut : [OK] Exe sur disque local
    )
) else (
    echo Statut : [ERREUR] Exe introuvable
)
echo.

REM 2. Taille de l'exe
echo [2/6] Taille de l'executable
echo --------------------------------

for %%A in ("%EXE_PATH%") do set "EXE_SIZE=%%~zA"
set /a "EXE_SIZE_MB=!EXE_SIZE! / 1048576"
echo Taille : !EXE_SIZE_MB! Mo

if !EXE_SIZE_MB! GTR 10 (
    echo Statut : [ATTENTION] Taille elevee
    echo Impact : +2-3 secondes au demarrage
) else (
    echo Statut : [OK] Taille normale
)
echo.

REM 3. Configuration MySQL
echo [3/6] Configuration MySQL
echo --------------------------------

set "ENV_FILE=%~dp0..\App\dist\EMAC\.env"
if exist "%ENV_FILE%" (
    for /f "tokens=1,2 delims==" %%a in ('type "%ENV_FILE%" 2^>nul') do (
        if "%%a"=="EMAC_DB_HOST" set "DB_HOST=%%b"
        if "%%a"=="EMAC_DB_NAME" set "DB_NAME=%%b"
    )

    echo Serveur : !DB_HOST!
    echo Base    : !DB_NAME!

    REM Tester ping
    echo Test ping vers !DB_HOST!...
    ping -n 1 !DB_HOST! >nul 2>&1
    if !errorlevel! EQU 0 (
        echo Statut : [OK] Serveur accessible
    ) else (
        echo Statut : [PROBLEME] Serveur inaccessible ou lent
        echo Solution : Verifier la connexion reseau
    )
) else (
    echo Statut : [ERREUR] Fichier .env introuvable
)
echo.

REM 4. Antivirus
echo [4/6] Antivirus
echo --------------------------------
echo IMPORTANT : Si l'antivirus scanne EMAC a chaque lancement,
echo cela peut provoquer des freezes de 5-10 secondes
echo.
echo Recommendation : Ajouter une exclusion pour
echo   %LOCALAPPDATA%\EMAC_Cache
echo.

REM 5. Cache local
echo [5/6] Cache local (Lancer_EMAC.bat)
echo --------------------------------

set "CACHE=%LOCALAPPDATA%\EMAC_Cache"
if exist "%CACHE%\EMAC.exe" (
    echo Statut : [OK] Cache local presente
    echo Emplacement : !CACHE!

    for %%A in ("%CACHE%\EMAC.exe") do set "CACHE_SIZE=%%~zA"
    set /a "CACHE_SIZE_MB=!CACHE_SIZE! / 1048576"
    echo Taille : !CACHE_SIZE_MB! Mo

    echo.
    echo Si vous utilisez Lancer_EMAC.bat, l'exe se lance depuis ce cache
    echo = Demarrage rapide (2-3 secondes)
) else (
    echo Statut : [ATTENTION] Pas de cache local
    echo.
    echo Vous n'avez jamais utilise Lancer_EMAC.bat
    echo ou le cache a ete supprime
    echo.
    echo Premier lancement avec le lanceur : 30-60 sec (copie)
    echo Lancements suivants : 2-3 sec
)
echo.

REM 6. Modules Python
echo [6/6] Modules Python charges
echo --------------------------------

set "INTERNAL=%~dp0..\App\dist\EMAC\_internal"
if exist "%INTERNAL%" (
    set "PYD_COUNT=0"
    for %%f in ("%INTERNAL%\*.pyd") do set /a PYD_COUNT+=1

    echo Modules natifs (.pyd) : !PYD_COUNT!
    if !PYD_COUNT! GTR 100 (
        echo Statut : [ATTENTION] Beaucoup de modules
        echo Impact : +5-10 secondes au demarrage
    ) else (
        echo Statut : [OK] Nombre normal
    )
)
echo.

REM ===================================================
REM RESUME ET RECOMMANDATIONS
REM ===================================================
echo.
echo ===================================================
echo   RESUME ET RECOMMANDATIONS
echo ===================================================
echo.

REM Calculer le score de problemes
set "SCORE_PROBLEME=0"

REM Probleme 1 : Exe sur reseau
echo !EXE_FULL! | findstr /C:"\\\\" >nul
if !errorlevel! EQU 0 (
    set /a SCORE_PROBLEME+=100
    echo [CRITIQUE] L'exe est lance depuis le reseau
    echo   Impact : +2-5 minutes au demarrage
    echo   Solution : Utiliser OBLIGATOIREMENT Lancer_EMAC.bat
    echo.
)

REM Probleme 2 : Pas de cache local
if not exist "%LOCALAPPDATA%\EMAC_Cache\EMAC.exe" (
    set /a SCORE_PROBLEME+=50
    echo [IMPORTANT] Aucun cache local detecte
    echo   Solution : Lancez Lancer_EMAC.bat au lieu de EMAC.exe
    echo.
)

REM Probleme 3 : Taille elevee
if !EXE_SIZE_MB! GTR 10 (
    set /a SCORE_PROBLEME+=10
    echo [MINEUR] Taille de l'exe elevee (!EXE_SIZE_MB! Mo)
    echo   Impact : +2-3 secondes au demarrage
    echo   Solution : Acceptable, pas de correction necessaire
    echo.
)

REM Afficher le verdict final
echo ===================================================
if !SCORE_PROBLEME! GTR 50 (
    echo   VERDICT : PROBLEME MAJEUR DETECTE
    echo ===================================================
    echo.
    echo La cause principale de la lenteur est identifiee.
    echo Suivez les recommandations ci-dessus pour corriger.
) else if !SCORE_PROBLEME! GTR 0 (
    echo   VERDICT : PROBLEMES MINEURS DETECTES
    echo ===================================================
    echo.
    echo La configuration est globalement correcte.
    echo Quelques optimisations sont possibles.
) else (
    echo   VERDICT : CONFIGURATION CORRECTE
    echo ===================================================
    echo.
    echo Aucun probleme majeur detecte.
    echo Si EMAC est toujours lent, contactez le support IT.
)

echo.
echo ===================================================
echo   ACTIONS IMMEDIATES
echo ===================================================
echo.
echo 1. Utilisez Lancer_EMAC.bat au lieu de EMAC.exe
echo    Emplacement : Deploy\Lancer_EMAC.bat
echo.
echo 2. Ajoutez une exclusion antivirus pour :
echo    %LOCALAPPDATA%\EMAC_Cache
echo.
echo 3. Verifiez la connexion MySQL avec :
echo    ping !DB_HOST!
echo.

goto :EOF
