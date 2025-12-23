@echo off
REM ===================================================
REM Generer un rapport de diagnostic EMAC
REM Version sans interaction
REM ===================================================

setlocal enabledelayedexpansion

set "RAPPORT=%~dp0diagnostic_rapport.txt"

echo Generation du diagnostic...
echo.

REM Generer le rapport
(
    echo ===================================================
    echo   DIAGNOSTIC DE LENTEUR EMAC
    echo   Date : %date% %time%
    echo ===================================================
    echo.

    REM 1. Emplacement
    echo [1/6] Emplacement d'execution
    echo --------------------------------

    set "EXE_PATH=%~dp0..\App\dist\EMAC\EMAC.exe"
    if exist "!EXE_PATH!" (
        for %%I in ("!EXE_PATH!") do set "EXE_FULL=%%~fI"
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

    REM 2. Taille
    echo [2/6] Taille de l'executable
    echo --------------------------------

    for %%A in ("!EXE_PATH!") do set "EXE_SIZE=%%~zA"
    set /a "EXE_SIZE_MB=!EXE_SIZE! / 1048576"
    echo Taille : !EXE_SIZE_MB! Mo

    if !EXE_SIZE_MB! GTR 10 (
        echo Statut : [ATTENTION] Taille elevee
        echo Impact : +2-3 secondes au demarrage
    ) else (
        echo Statut : [OK] Taille normale
    )
    echo.

    REM 3. MySQL
    echo [3/6] Configuration MySQL
    echo --------------------------------

    set "ENV_FILE=%~dp0..\App\dist\EMAC\.env"
    if exist "!ENV_FILE!" (
        for /f "tokens=1,2 delims==" %%a in ('type "!ENV_FILE!" 2^>nul') do (
            if "%%a"=="EMAC_DB_HOST" set "DB_HOST=%%b"
            if "%%a"=="EMAC_DB_NAME" set "DB_NAME=%%b"
        )

        echo Serveur : !DB_HOST!
        echo Base    : !DB_NAME!

        ping -n 1 !DB_HOST! >nul 2>&1
        if !errorlevel! EQU 0 (
            echo Statut : [OK] Serveur accessible
        ) else (
            echo Statut : [PROBLEME] Serveur inaccessible ou lent
        )
    ) else (
        echo Statut : [ERREUR] Fichier .env introuvable
    )
    echo.

    REM 4. Antivirus
    echo [4/6] Antivirus
    echo --------------------------------
    echo Recommendation : Ajouter une exclusion pour
    echo   %%LOCALAPPDATA%%\EMAC_Cache
    echo.

    REM 5. Cache local
    echo [5/6] Cache local
    echo --------------------------------

    set "CACHE=%LOCALAPPDATA%\EMAC_Cache"
    if exist "!CACHE!\EMAC.exe" (
        echo Statut : [OK] Cache local presente
        echo Emplacement : !CACHE!

        for %%A in ("!CACHE!\EMAC.exe") do set "CACHE_SIZE=%%~zA"
        set /a "CACHE_SIZE_MB=!CACHE_SIZE! / 1048576"
        echo Taille : !CACHE_SIZE_MB! Mo
        echo.
        echo Si vous utilisez Lancer_EMAC.bat :
        echo   = Demarrage rapide (2-3 secondes^)
    ) else (
        echo Statut : [ATTENTION] Pas de cache local
        echo.
        echo Vous n'avez jamais utilise Lancer_EMAC.bat
        echo Premier lancement : 30-60 sec (copie^)
        echo Lancements suivants : 2-3 sec
    )
    echo.

    REM 6. Modules
    echo [6/6] Modules Python
    echo --------------------------------

    set "INTERNAL=%~dp0..\App\dist\EMAC\_internal"
    if exist "!INTERNAL!" (
        set "PYD_COUNT=0"
        for %%f in ("!INTERNAL!\*.pyd") do set /a PYD_COUNT+=1

        echo Modules natifs (.pyd^) : !PYD_COUNT!
        if !PYD_COUNT! GTR 100 (
            echo Statut : [ATTENTION] Beaucoup de modules
        ) else (
            echo Statut : [OK] Nombre normal
        )
    )
    echo.

    REM VERDICT
    echo ===================================================
    echo   VERDICT ET RECOMMANDATIONS
    echo ===================================================
    echo.

    REM Detecter les problemes
    set "PROBLEME_RESEAU=0"
    set "PROBLEME_CACHE=0"

    echo !EXE_FULL! | findstr /C:"\\\\" >nul
    if !errorlevel! EQU 0 set "PROBLEME_RESEAU=1"

    if not exist "!CACHE!\EMAC.exe" set "PROBLEME_CACHE=1"

    if !PROBLEME_RESEAU!==1 (
        echo [CRITIQUE] L'exe est lance depuis le reseau
        echo   Impact : +2-5 minutes au demarrage
        echo   Solution : Utiliser OBLIGATOIREMENT Lancer_EMAC.bat
        echo.
    )

    if !PROBLEME_CACHE!==1 (
        echo [IMPORTANT] Aucun cache local detecte
        echo   Solution : Lancez Lancer_EMAC.bat
        echo.
    )

    if !PROBLEME_RESEAU!==0 if !PROBLEME_CACHE!==0 (
        echo [OK] Configuration correcte
        echo   Si EMAC est toujours lent, verifiez :
        echo   - Exclusion antivirus pour %%LOCALAPPDATA%%\EMAC_Cache
        echo   - Connexion MySQL (ping !DB_HOST!^)
        echo.
    )

    echo ===================================================
    echo   ACTIONS IMMEDIATES
    echo ===================================================
    echo.
    echo 1. Utilisez Lancer_EMAC.bat au lieu de EMAC.exe
    echo 2. Ajoutez exclusion antivirus : %%LOCALAPPDATA%%\EMAC_Cache
    echo 3. Verifiez MySQL : ping !DB_HOST!
    echo.

) > "%RAPPORT%"

REM Afficher le resultat
cls
echo.
echo ===================================================
echo   DIAGNOSTIC TERMINE
echo ===================================================
echo.
echo Le rapport a ete sauvegarde dans :
echo %RAPPORT%
echo.
echo.

REM Afficher le contenu
type "%RAPPORT%"

echo.
echo ===================================================
echo.
echo Voulez-vous ouvrir le fichier dans Notepad ? (O/N)
choice /c ON /n /m "Reponse : "

if errorlevel 2 goto :FIN
if errorlevel 1 notepad "%RAPPORT%"

:FIN
echo.
echo Au revoir !
exit /b 0
