@echo off
REM ===================================================
REM Diagnostic de lenteur EMAC
REM ===================================================

setlocal enabledelayedexpansion

REM Creer le fichier de rapport
set "RAPPORT=%~dp0diagnostic_rapport.txt"
echo. > "%RAPPORT%"
echo =================================================== >> "%RAPPORT%"
echo   DIAGNOSTIC DE LENTEUR EMAC >> "%RAPPORT%"
echo   Date : %date% %time% >> "%RAPPORT%"
echo =================================================== >> "%RAPPORT%"
echo. >> "%RAPPORT%"

cls
echo.
echo ===================================================
echo   DIAGNOSTIC DE LENTEUR EMAC
echo ===================================================
echo.
echo   Le rapport sera sauvegarde dans :
echo   %RAPPORT%
echo.

REM 1. Verifier d'ou est lance l'exe
echo [1/6] Verification de l'emplacement d'execution...
echo [1/6] Verification de l'emplacement d'execution... >> "%RAPPORT%"
echo. >> "%RAPPORT%"

set "EXE_PATH=%~dp0..\App\dist\EMAC\EMAC.exe"
if exist "%EXE_PATH%" (
    for %%I in ("%EXE_PATH%") do set "EXE_FULL=%%~fI"
    echo    Chemin de l'exe : !EXE_FULL!
    echo    Chemin de l'exe : !EXE_FULL! >> "%RAPPORT%"

    REM Verifier si c'est sur le reseau
    echo !EXE_FULL! | findstr /C:"\\\\" >nul
    if !errorlevel! EQU 0 (
        echo    [PROBLEME] L'exe est sur un partage reseau !
        echo    [PROBLEME] L'exe est sur un partage reseau ! >> "%RAPPORT%"
        echo               Cela explique la lenteur (2-5 min de demarrage)
        echo               Cela explique la lenteur (2-5 min de demarrage) >> "%RAPPORT%"
        echo. >> "%RAPPORT%"
        echo    Solution : Utilisez Lancer_EMAC.bat qui copie sur le disque local
        echo    Solution : Utilisez Lancer_EMAC.bat qui copie sur le disque local >> "%RAPPORT%"
    ) else (
        echo    [OK] L'exe est sur le disque local
        echo    [OK] L'exe est sur le disque local >> "%RAPPORT%"
    )
) else (
    echo    [ERREUR] Exe introuvable
    echo    [ERREUR] Exe introuvable >> "%RAPPORT%"
)
echo.
echo. >> "%RAPPORT%"
timeout /t 2 /nobreak >nul

REM 2. Verifier la taille de l'exe
echo [2/6] Verification de la taille de l'executable...
echo.

for %%A in ("%EXE_PATH%") do set "EXE_SIZE=%%~zA"
set /a "EXE_SIZE_MB=!EXE_SIZE! / 1048576"
echo    Taille : !EXE_SIZE_MB! Mo
if !EXE_SIZE_MB! GTR 10 (
    echo    [ATTENTION] Taille elevee (peut rallonger le demarrage de 2-3s)
) else (
    echo    [OK] Taille normale
)
echo.
timeout /t 2 /nobreak >nul

REM 3. Verifier la connexion MySQL
echo [3/6] Test de connexion a la base de donnees...
echo.

REM Lire le .env
set "ENV_FILE=%~dp0..\App\dist\EMAC\.env"
if exist "%ENV_FILE%" (
    for /f "tokens=1,2 delims==" %%a in ('type "%ENV_FILE%"') do (
        if "%%a"=="EMAC_DB_HOST" set "DB_HOST=%%b"
        if "%%a"=="EMAC_DB_NAME" set "DB_NAME=%%b"
    )

    echo    Serveur : !DB_HOST!
    echo    Base    : !DB_NAME!
    echo.

    REM Tester ping
    ping -n 1 !DB_HOST! >nul 2>&1
    if !errorlevel! EQU 0 (
        echo    [OK] Serveur accessible (ping OK)
    ) else (
        echo    [PROBLEME] Serveur inaccessible ou lent !
        echo               Verifiez la connexion reseau vers !DB_HOST!
    )
) else (
    echo    [ERREUR] Fichier .env introuvable
)
echo.
timeout /t 2 /nobreak >nul

REM 4. Verifier l'antivirus
echo [4/6] Verification de l'antivirus...
echo.

echo    IMPORTANT : Si l'antivirus scanne l'exe a chaque lancement,
echo               cela peut provoquer des freezes de 5-10 secondes
echo.
echo    Verifiez si EMAC.exe est exclu de l'antivirus :
echo    - Windows Defender : Parametres ^> Protection ^> Exclusions
echo    - Ajoutez : %LOCALAPPDATA%\EMAC_Cache
echo.
timeout /t 3 /nobreak >nul

REM 5. Verifier les imports Python lourds
echo [5/6] Analyse des modules charges...
echo.

set "INTERNAL=%~dp0..\App\dist\EMAC\_internal"
if exist "%INTERNAL%" (
    REM Compter les fichiers .pyd (extensions Python compilees)
    set "PYD_COUNT=0"
    for %%f in ("%INTERNAL%\*.pyd") do set /a PYD_COUNT+=1

    echo    Modules natifs (.pyd) : !PYD_COUNT!
    if !PYD_COUNT! GTR 100 (
        echo    [ATTENTION] Beaucoup de modules (ralentit le demarrage)
    ) else (
        echo    [OK] Nombre normal de modules
    )

    REM Verifier les gros fichiers
    echo.
    echo    Fichiers les plus lourds dans _internal :
    dir /b /o-s "%INTERNAL%\*" 2>nul | findstr /V /C:"base_library" | head -5
)
echo.
timeout /t 2 /nobreak >nul

REM 6. Mesurer le temps de demarrage
echo [6/6] Test de vitesse de demarrage...
echo.
echo    Lancement de EMAC.exe (mode test)...
echo    Temps de demarrage mesure...
echo.

set "START_TIME=%time%"
echo    Debut : %START_TIME%

REM Lancer l'exe en tache de fond
start "" "%EXE_PATH%"

echo.
echo    [ATTENDEZ] L'application se lance...
echo    Observez :
echo    - Temps avant que la fenetre apparaisse
echo    - Freezes pendant la saisie de texte
echo.

timeout /t 5 /nobreak >nul

set "END_TIME=%time%"
echo    Fin : %END_TIME%

REM Afficher les recommandations
echo.
echo ===================================================
echo   RECOMMANDATIONS
echo ===================================================
echo.

echo 1. Si vous lancez depuis le reseau :
echo    ^> Utilisez OBLIGATOIREMENT Lancer_EMAC.bat
echo    ^> Premier lancement : 30-60s (copie locale)
echo    ^> Lancements suivants : 2-3s
echo.

echo 2. Si les freezes persistent meme en local :
echo    ^> Ajoutez %%LOCALAPPDATA%%\EMAC_Cache aux exclusions antivirus
echo    ^> Verifiez la connexion a MySQL (!DB_HOST!)
echo    ^> Desactivez les logs de debug si actives
echo.

echo 3. Si le serveur MySQL est lent :
echo    ^> Verifiez le ping : ping !DB_HOST!
echo    ^> Optimisez la base de donnees (indexes)
echo    ^> Utilisez un serveur MySQL local si possible
echo.

echo ===================================================
echo.
pause
