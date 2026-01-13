@echo off
REM ============================================================================
REM EMAC - Script de Build PyInstaller Optimisé
REM ============================================================================
REM
REM Ce script compile l'application EMAC en un exécutable Windows optimisé
REM
REM Prérequis:
REM   - Python 3.x installé
REM   - PyInstaller installé (pip install pyinstaller)
REM   - Toutes les dépendances installées (pip install -r App/requirements.txt)
REM
REM Usage:
REM   build.bat
REM
REM Sortie:
REM   dist/EMAC/EMAC.exe
REM
REM ============================================================================

echo.
echo ============================================================================
echo                    EMAC - BUILD PYINSTALLER OPTIMISE
echo ============================================================================
echo.

REM Vérifier que Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    echo.
    echo Installez Python depuis https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Vérifier que PyInstaller est installé
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] PyInstaller n'est pas installe
    echo.
    echo Installation en cours...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERREUR] Impossible d'installer PyInstaller
        pause
        exit /b 1
    )
)

REM Afficher les versions
echo [INFO] Versions des outils:
python --version
python -c "import PyInstaller; print(f'PyInstaller {PyInstaller.__version__}')"
echo.

REM Nettoyer les anciens builds
echo [1/5] Nettoyage des anciens builds...
if exist "build\" (
    rmdir /S /Q "build\"
    echo   - build\ supprime
)
if exist "dist\" (
    rmdir /S /Q "dist\"
    echo   - dist\ supprime
)
if exist "App\core\gui\build\" (
    rmdir /S /Q "App\core\gui\build\"
    echo   - App\core\gui\build\ supprime
)
if exist "App\core\gui\dist\" (
    rmdir /S /Q "App\core\gui\dist\"
    echo   - App\core\gui\dist\ supprime
)
echo   [OK] Nettoyage termine
echo.

REM Vérifier la configuration .env
echo [2/5] Verification de la configuration...
if not exist "App\.env" (
    echo   [AVERTISSEMENT] Fichier App\.env manquant
    echo   L'application ne pourra pas se connecter a la base de donnees
    echo.
    echo   Creez App\.env a partir de App\config\.env.example
    echo   Voir: docs/security/database-credentials.md
    echo.
    set /p continue="   Continuer quand meme? (O/N): "
    if /i not "!continue!"=="O" (
        echo   Build annule
        pause
        exit /b 1
    )
)
echo   [OK] Configuration verifiee
echo.

REM Lancer PyInstaller
echo [3/5] Lancement de PyInstaller...
echo   Mode: One-folder optimise
echo   Spec: EMAC.spec
echo.
echo   Cela peut prendre 2-3 minutes...
echo.

pyinstaller --clean --noconfirm EMAC.spec

if errorlevel 1 (
    echo.
    echo [ERREUR] Le build a echoue
    echo.
    echo Verifiez:
    echo   1. Toutes les dependances sont installees (pip install -r App\requirements.txt)
    echo   2. Le fichier EMAC.spec est valide
    echo   3. Pas de fichiers Python avec erreurs de syntaxe
    echo.
    pause
    exit /b 1
)

echo.
echo   [OK] Build termine avec succes
echo.

REM Vérifier la sortie
echo [4/5] Verification de la sortie...
if not exist "dist\EMAC\EMAC.exe" (
    echo   [ERREUR] L'executable n'a pas ete cree
    pause
    exit /b 1
)

REM Calculer la taille
for %%A in ("dist\EMAC\EMAC.exe") do set "EXE_SIZE=%%~zA"
for /f %%A in ('dir /s /a "dist\EMAC" ^| findstr /C:"octets" ^| findstr /C:"fichiers"') do set "TOTAL_SIZE=%%A"

echo   [OK] Executable cree: dist\EMAC\EMAC.exe
echo   Taille: %EXE_SIZE% octets
echo.

REM Créer un fichier README dans dist
echo [5/5] Creation du README...
(
echo EMAC - Application de Gestion du Personnel
echo ==========================================
echo.
echo Version: Build optimise %DATE% %TIME%
echo.
echo Execution:
echo   1. Double-cliquez sur EMAC.exe
echo   2. Connectez-vous avec vos identifiants
echo.
echo Configuration:
echo   - La base de donnees doit etre accessible
echo   - Le fichier .env doit etre configure
echo.
echo Support:
echo   Voir la documentation dans le repertoire docs/
echo.
) > "dist\EMAC\README.txt"

echo   [OK] README cree
echo.

REM Résumé final
echo ============================================================================
echo                              BUILD TERMINE
echo ============================================================================
echo.
echo   Executable: dist\EMAC\EMAC.exe
echo   Dossier: dist\EMAC\
echo.
echo   Pour distribuer l'application:
echo     1. Copiez tout le dossier dist\EMAC\ (pas seulement EMAC.exe)
echo     2. Assurez-vous que le fichier .env est configure sur le PC cible
echo     3. La base de donnees MySQL doit etre accessible
echo.
echo   Pour tester:
echo     cd dist\EMAC
echo     EMAC.exe
echo.
echo ============================================================================
echo.

REM Proposer d'ouvrir le dossier
set /p open="Voulez-vous ouvrir le dossier dist\EMAC? (O/N): "
if /i "%open%"=="O" (
    explorer "dist\EMAC"
)

echo.
pause
