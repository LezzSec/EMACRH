@echo off
REM Script de build pour créer l'exécutable EMAC avec PyInstaller
REM Alternative à cx_Freeze - plus simple et plus robuste

echo =====================================
echo  Build EMAC - PyInstaller
echo =====================================
echo.

REM Vérifier si PyInstaller est installé
echo [1/4] Vérification de PyInstaller...
py -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo PyInstaller n'est pas installé.
    echo Installation en cours...
    py -m pip install pyinstaller
    if %errorlevel% neq 0 (
        echo ERREUR: Échec de l'installation de PyInstaller
        pause
        exit /b 1
    )
)
echo OK - PyInstaller est installé
echo.

REM Nettoyer les anciens builds
echo [2/4] Nettoyage des anciens builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo OK - Nettoyage effectué
echo.

REM Créer l'exécutable
echo [3/4] Création de l'exécutable avec le fichier .spec...
echo Cela peut prendre 2-3 minutes...
echo.

pyinstaller --clean --noconfirm EMAC.spec

if %errorlevel% neq 0 (
    echo ERREUR: Échec de la création de l'exécutable
    pause
    exit /b 1
)
echo OK - Exécutable créé
echo.

REM Créer les dossiers nécessaires
echo [4/4] Finalisation...
if not exist dist\EMAC\logs mkdir dist\EMAC\logs
if not exist dist\EMAC\database\backups mkdir dist\EMAC\database\backups

REM Créer un fichier .env.example
echo # Configuration de la base de données EMAC > dist\EMAC\.env.example
echo # Copier ce fichier en ".env" et remplir avec vos vraies valeurs >> dist\EMAC\.env.example
echo. >> dist\EMAC\.env.example
echo EMAC_DB_HOST=localhost >> dist\EMAC\.env.example
echo EMAC_DB_USER=root >> dist\EMAC\.env.example
echo EMAC_DB_PASSWORD=VotreMotDePasse >> dist\EMAC\.env.example
echo EMAC_DB_NAME=emac_db >> dist\EMAC\.env.example

echo OK - Build finalisé
echo.

echo =====================================
echo  Build terminé avec succès !
echo =====================================
echo.
echo L'exécutable se trouve dans : dist\EMAC\
echo Fichier principal : dist\EMAC\EMAC.exe
echo.
echo Pour tester l'exécutable :
echo   cd dist\EMAC
echo   EMAC.exe
echo.
pause
