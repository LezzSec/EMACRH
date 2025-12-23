@echo off
REM ========================================
REM EMAC - Lanceur Réseau Optimisé
REM Version 1.0
REM ========================================

setlocal enabledelayedexpansion

REM ⚙️ CONFIGURATION - Chemin vers l'application EMAC
REM Pour developpement local : pointe vers le dossier dist\EMAC
REM Pour production reseau : utiliser \\serveur\partage\EMAC
set "SOURCE_RESEAU=%~dp0..\App\dist\EMAC"

REM Variables système (ne pas modifier)
set "CACHE_LOCAL=%LOCALAPPDATA%\EMAC_Cache"
set "LOG_FILE=%CACHE_LOCAL%\launcher.log"

REM Créer le dossier de logs
if not exist "%CACHE_LOCAL%" mkdir "%CACHE_LOCAL%"

echo. > "%LOG_FILE%"
echo ================================================ >> "%LOG_FILE%"
echo EMAC Launcher - %date% %time% >> "%LOG_FILE%"
echo ================================================ >> "%LOG_FILE%"

REM Interface utilisateur
cls
echo.
echo  ================================================
echo    EMAC - Gestion Personnel et Polyvalence
echo  ================================================
echo.

REM 1. Vérifier que le partage réseau est accessible
if not exist "%SOURCE_RESEAU%\EMAC.exe" (
    echo  ❌ ERREUR : Application non trouvée sur le réseau
    echo.
    echo     Chemin configuré : %SOURCE_RESEAU%
    echo.
    echo     Veuillez vérifier :
    echo     1. Le serveur est accessible
    echo     2. Le chemin réseau est correct
    echo     3. Vous avez les droits d'accès
    echo.
    echo  >> "%LOG_FILE%" 2>&1
    echo ERREUR: Source réseau inaccessible : %SOURCE_RESEAU% >> "%LOG_FILE%"
    pause
    exit /b 1
)

REM 2. Déterminer si copie nécessaire
set "NEED_COPY=0"
set "COPY_REASON=Première installation"

if not exist "%CACHE_LOCAL%\EMAC.exe" (
    set "NEED_COPY=1"
    set "COPY_REASON=Première installation"
    echo  📦 Première installation détectée >> "%LOG_FILE%"
) else (
    REM Comparer les tailles de fichiers
    for %%A in ("%SOURCE_RESEAU%\EMAC.exe") do set "SIZE_RESEAU=%%~zA"
    for %%B in ("%CACHE_LOCAL%\EMAC.exe") do set "SIZE_LOCAL=%%~zB"

    if not "!SIZE_RESEAU!"=="!SIZE_LOCAL!" (
        set "NEED_COPY=1"
        set "COPY_REASON=Mise à jour disponible (taille différente)"
        echo  🔄 Mise à jour détectée (taille: !SIZE_RESEAU! vs !SIZE_LOCAL!) >> "%LOG_FILE%"
    ) else (
        REM Comparer les dates
        for %%A in ("%SOURCE_RESEAU%\EMAC.exe") do set "DATE_RESEAU=%%~tA"
        for %%B in ("%CACHE_LOCAL%\EMAC.exe") do set "DATE_LOCAL=%%~tB"

        if not "!DATE_RESEAU!"=="!DATE_LOCAL!" (
            set "NEED_COPY=1"
            set "COPY_REASON=Mise à jour disponible (date différente)"
            echo  🔄 Mise à jour détectée (date modifiée) >> "%LOG_FILE%"
        )
    )
)

REM 3. Copier si nécessaire
if "%NEED_COPY%"=="1" (
    echo  ⏳ %COPY_REASON%...
    echo  📂 Copie depuis le réseau vers le disque local
    echo     (Cela peut prendre 30-60 secondes)
    echo.

    echo Début de la copie : %time% >> "%LOG_FILE%"

    REM Utiliser robocopy pour copie efficace
    robocopy "%SOURCE_RESEAU%" "%CACHE_LOCAL%" /MIR /R:2 /W:5 /NFL /NDL /NJH /NJS /NP >> "%LOG_FILE%" 2>&1

    set "ROBOCOPY_EXIT=%errorlevel%"
    echo Robocopy exit code: !ROBOCOPY_EXIT! >> "%LOG_FILE%"

    REM Robocopy return codes: 0-7 = success, 8+ = error
    if !ROBOCOPY_EXIT! GEQ 8 (
        echo.
        echo  ❌ ERREUR : Échec de la copie depuis le réseau
        echo.
        echo     Code d'erreur : !ROBOCOPY_EXIT!
        echo     Consultez : %LOG_FILE%
        echo.
        echo ERREUR: Robocopy failed with code !ROBOCOPY_EXIT! >> "%LOG_FILE%"
        pause
        exit /b 1
    )

    echo Fin de la copie : %time% >> "%LOG_FILE%"
    echo  ✅ Copie terminée
    echo.
) else (
    echo  ✅ Version locale à jour
    echo  📁 Lancement depuis : %CACHE_LOCAL%
    echo.
    echo Version locale à jour, pas de copie nécessaire >> "%LOG_FILE%"
)

REM 4. Vérifier que .env existe
if not exist "%CACHE_LOCAL%\.env" (
    echo  ⚠️  ATTENTION : Fichier .env manquant
    echo     L'application risque de ne pas démarrer
    echo.
    echo WARNING: .env file missing in cache >> "%LOG_FILE%"
)

REM 5. Lancer l'application
echo  🚀 Lancement d'EMAC...
echo.
echo Lancement de l'application : %time% >> "%LOG_FILE%"
echo Commande : "%CACHE_LOCAL%\EMAC.exe" >> "%LOG_FILE%"

cd /d "%CACHE_LOCAL%"
start "" "%CACHE_LOCAL%\EMAC.exe"

if errorlevel 1 (
    echo.
    echo  ❌ ERREUR : Impossible de lancer l'application
    echo     Consultez : %LOG_FILE%
    echo.
    echo ERREUR: Failed to start EMAC.exe >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo  ✅ Application lancée avec succès
echo Application started successfully >> "%LOG_FILE%"
echo.

REM Attendre 2 secondes puis fermer
timeout /t 2 /nobreak >nul
exit /b 0
