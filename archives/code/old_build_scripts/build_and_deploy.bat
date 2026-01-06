@echo off
REM ===============================================================
REM   SCRIPT COMPLET : BUILD + COPIE VERS PARTAGE RESEAU
REM ===============================================================
REM
REM Ce script :
REM 1. Nettoie les anciens builds
REM 2. Compile l'exe optimisé (one-folder)
REM 3. Copie le .env et les ressources nécessaires
REM 4. Propose de copier vers le partage réseau
REM
REM ===============================================================

setlocal enabledelayedexpansion

echo.
echo ===============================================================
echo   COMPILATION EMAC - VERSION OPTIMISEE + DEPLOIEMENT
echo ===============================================================
echo.

REM ============================================================
REM   ETAPE 1 : Nettoyage
REM ============================================================
echo [1/5] Nettoyage des anciens builds...
if exist build (
    echo    - Suppression du dossier build...
    rmdir /s /q build
)
if exist dist\EMAC (
    echo    - Suppression du dossier dist\EMAC...
    rmdir /s /q dist\EMAC
)
echo    ✓ Nettoyage terminé
echo.

REM ============================================================
REM   ETAPE 2 : Compilation avec PyInstaller
REM ============================================================
echo [2/5] Compilation avec PyInstaller (mode one-folder optimisé)...
echo.
pyinstaller EMAC_optimized.spec --clean --noconfirm

REM Vérifier que la compilation a réussi
if not exist dist\EMAC\EMAC.exe (
    echo.
    echo ❌ ERREUR : La compilation a échoué
    echo    L'exécutable dist\EMAC\EMAC.exe n'a pas été créé
    echo.
    pause
    exit /b 1
)
echo.
echo    ✓ Compilation réussie : dist\EMAC\EMAC.exe créé
echo.

REM ============================================================
REM   ETAPE 3 : Copie des fichiers de configuration
REM ============================================================
echo [3/5] Copie des fichiers de configuration...

REM Copier le .env (CRITIQUE pour la DB)
if exist ".env" (
    copy /y ".env" "dist\EMAC\.env" >nul
    echo    ✓ .env copié dans dist\EMAC\
) else if exist "config\.env" (
    copy /y "config\.env" "dist\EMAC\.env" >nul
    echo    ✓ config\.env copié dans dist\EMAC\
) else (
    echo    ⚠️  ATTENTION : Aucun fichier .env trouvé !
    echo       L'exe nécessite EMAC_DB_PASSWORD configuré
    echo.
)

REM Copier les fichiers SQL si nécessaire (optionnel)
REM if exist database\schema (
REM     xcopy /s /i /y database\schema dist\EMAC\database\schema >nul
REM     echo    ✓ Schémas SQL copiés
REM )

echo.

REM ============================================================
REM   ETAPE 4 : Informations sur le build
REM ============================================================
echo [4/5] Informations sur le build...
echo.
echo    Dossier de sortie : %CD%\dist\EMAC
echo    Exécutable : EMAC.exe
echo.

REM Afficher la taille du dossier
for /f "tokens=3" %%a in ('dir dist\EMAC /s ^| find "octets"') do set SIZE=%%a
echo    Taille totale : %SIZE% octets
echo.

REM Lister les fichiers principaux
echo    Fichiers principaux :
dir /b dist\EMAC\EMAC.exe 2>nul && echo       - EMAC.exe
dir /b dist\EMAC\.env 2>nul && echo       - .env
dir /b dist\EMAC\_internal 2>nul && echo       - _internal\ (bibliothèques)
echo.

REM ============================================================
REM   ETAPE 5 : Proposition de copie vers le réseau
REM ============================================================
echo [5/5] Déploiement vers le partage réseau...
echo.
echo    Voulez-vous copier l'application vers le partage réseau ?
echo.
echo    Options disponibles :
echo      1) Copier vers un chemin personnalisé
echo      2) Tester localement seulement (sauter la copie)
echo      3) Annuler
echo.

set /p DEPLOY_CHOICE="    Votre choix (1/2/3) : "

if "%DEPLOY_CHOICE%"=="1" (
    echo.
    set /p NETWORK_PATH="    Entrez le chemin du partage réseau (ex: Z:\EMAC ou \\serveur\partage\EMAC) : "

    if "!NETWORK_PATH!"=="" (
        echo.
        echo    ⚠️  Aucun chemin saisi, copie annulée
        goto :END_DEPLOY
    )

    echo.
    echo    Copie vers : !NETWORK_PATH!
    echo.

    REM Créer le dossier si nécessaire
    if not exist "!NETWORK_PATH!" (
        mkdir "!NETWORK_PATH!" 2>nul
        if errorlevel 1 (
            echo    ❌ ERREUR : Impossible de créer le dossier !NETWORK_PATH!
            echo       Vérifiez les permissions et le chemin réseau
            goto :END_DEPLOY
        )
    )

    REM Copier tout le contenu de dist\EMAC vers le réseau
    echo    Copie en cours...
    xcopy /s /e /i /y "dist\EMAC" "!NETWORK_PATH!" >nul

    if errorlevel 1 (
        echo    ❌ ERREUR : La copie vers le réseau a échoué
        echo       Vérifiez que le partage est accessible
    ) else (
        echo    ✓ Copie réussie vers !NETWORK_PATH!
        echo.
        echo    Vous pouvez maintenant lancer : !NETWORK_PATH!\EMAC.exe
    )
) else if "%DEPLOY_CHOICE%"=="2" (
    echo.
    echo    ✓ Copie réseau ignorée (test local uniquement)
) else (
    echo.
    echo    ✓ Déploiement annulé
)

:END_DEPLOY

echo.
echo ===============================================================
echo   ✅ PROCESSUS TERMINE
echo ===============================================================
echo.
echo   Executable local : %CD%\dist\EMAC\EMAC.exe
echo.
echo   Pour tester localement :
echo     cd dist\EMAC
echo     EMAC.exe
echo.
echo   IMPORTANT - Configuration réseau :
echo     - L'exe doit être copié sur un disque LOCAL (C:, D:, etc.)
echo     - OU utiliser un lecteur réseau mappé (Z:, Y:, etc.)
echo     - NE PAS lancer directement depuis \\serveur\partage
echo.
echo   IMPORTANT - Base de données :
echo     - Le fichier .env doit contenir EMAC_DB_PASSWORD
echo     - MySQL doit être accessible depuis le poste client
echo.

pause
