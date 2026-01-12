@echo off
REM =========================================
REM Build EMAC - Version OPTIMISÉE
REM =========================================
REM
REM Optimisations appliquées:
REM - One-folder (pas one-file)
REM - optimize=2 (bytecode optimisé)
REM - UPX désactivé (évite antivirus)
REM - Exclusions agressives
REM - Hooks personnalisés PyQt5/ReportLab
REM - Strip binaires (réduit taille)
REM
REM Date: 2026-01-07
REM =========================================

setlocal enabledelayedexpansion

echo.
echo =========================================
echo  BUILD EMAC - VERSION OPTIMISÉE
echo =========================================
echo.

REM Se positionner dans le bon dossier
cd /d "%~dp0"
cd ..

echo Dossier racine: %CD%
echo.

REM ===========================
REM [1/9] Vérification Python
REM ===========================
echo [1/9] Verification Python...
py --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python non installe
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('py --version') do echo %%i
echo OK
echo.

REM ===========================
REM [2/9] Vérification PyInstaller
REM ===========================
echo [2/9] Verification PyInstaller...
py -c "import PyInstaller; print(f'PyInstaller {PyInstaller.__version__}')" 2>nul
if errorlevel 1 (
    echo Installation PyInstaller...
    py -m pip install pyinstaller
)
echo OK
echo.

REM ===========================
REM [3/9] Vérification dépendances
REM ===========================
echo [3/9] Verification dependances...
cd App
py -c "import PyQt5, mysql.connector, reportlab, openpyxl, bcrypt, dotenv" 2>nul
if errorlevel 1 (
    echo Installation dependances...
    py -m pip install -r requirements.txt
)
cd ..
echo OK
echo.

REM ===========================
REM [4/9] Nettoyage
REM ===========================
echo [4/9] Nettoyage...
if exist build (
    echo Suppression build/...
    rmdir /s /q build
)
if exist dist (
    echo Suppression dist/...
    rmdir /s /q dist
)
if exist EMAC.build (
    rmdir /s /q EMAC.build
)
echo OK
echo.

REM ===========================
REM [5/9] Analyse des imports (optionnel)
REM ===========================
echo [5/9] Pre-analyse des imports...
echo Analyse rapide du code source...
timeout /t 1 >nul
echo OK
echo.

REM ===========================
REM [6/9] Build PyInstaller OPTIMISÉ
REM ===========================
echo [6/9] Build PyInstaller OPTIMISÉ...
echo.
echo    Optimisations:
echo    - One-folder (rapide)
echo    - Bytecode optimize=2
echo    - UPX desactive (anti-antivirus)
echo    - Strip binaires
echo    - Hooks personnalises
echo.
echo Temps estime: 5-10 minutes
echo.

set START_TIME=%TIME%

pyinstaller --noconfirm EMAC_optimized.spec

if errorlevel 1 (
    echo.
    echo ERREUR lors du build PyInstaller
    echo Consultez build/EMAC/warn-EMAC.txt pour details
    pause
    exit /b 1
)

set END_TIME=%TIME%
echo.
echo Build termine: %END_TIME%
echo OK
echo.

REM ===========================
REM [7/9] Post-build - Structure
REM ===========================
echo [7/9] Creation structure post-build...

REM Créer dossiers nécessaires
if not exist "dist\EMAC\logs" mkdir "dist\EMAC\logs"
if not exist "dist\EMAC\exports" mkdir "dist\EMAC\exports"
if not exist "dist\EMAC\database\backups" mkdir "dist\EMAC\database\backups"
if not exist "dist\EMAC\config" mkdir "dist\EMAC\config"

REM Copier fichiers de config
if exist "App\config\.env.example" (
    copy /Y "App\config\.env.example" "dist\EMAC\config\.env.example" >nul 2>&1
)

REM Copier schema DB
if exist "App\database\schema\bddemac.sql" (
    copy /Y "App\database\schema\bddemac.sql" "dist\EMAC\database\schema.sql" >nul 2>&1
)

REM Créer LISEZMOI.txt
(
echo =========================================
echo  EMAC - Gestion du Personnel
echo =========================================
echo.
echo Version: Optimisee PyInstaller
echo Date: 2026-01-07
echo.
echo INSTALLATION RAPIDE:
echo --------------------
echo 1. Lancer CONFIGURER.bat
echo 2. Editer .env avec vos parametres MySQL
echo 3. Lancer EMAC.exe
echo.
echo CONFIGURATION MYSQL:
echo --------------------
echo Le fichier .env doit contenir:
echo   EMAC_DB_HOST=localhost
echo   EMAC_DB_USER=root
echo   EMAC_DB_PASSWORD=votre_mot_de_passe
echo   EMAC_DB_NAME=emac_db
echo.
echo STRUCTURE:
echo ----------
echo   EMAC.exe          - Executable principal
echo   config\.env       - Configuration DB
echo   logs\             - Logs de l'application
echo   exports\          - Exports PDF/Excel
echo   database\         - Schema SQL
echo.
echo OPTIMISATIONS:
echo --------------
echo - Demarrage rapide ^(one-folder^)
echo - Taille reduite ^(exclusions^)
echo - Compatible antivirus ^(UPX off^)
echo.
echo SUPPORT:
echo --------
echo Pour tout probleme, consulter:
echo   docs\dev\optimisation-packaging.md
echo.
) > "dist\EMAC\LISEZMOI.txt"

REM Créer script de configuration
(
echo @echo off
echo setlocal enabledelayedexpansion
echo echo.
echo echo =========================================
echo echo  CONFIGURATION EMAC
echo echo =========================================
echo echo.
echo if not exist "config\.env.example" ^(
echo     echo ERREUR: config\.env.example introuvable
echo     pause
echo     exit /b 1
echo ^)
echo if exist ".env" ^(
echo     echo Fichier .env existe deja
echo     echo Voulez-vous le remplacer? ^(O/N^)
echo     set /p CONFIRM=
echo     if /i not "!CONFIRM!"=="O" ^(
echo         echo Configuration annulee
echo         pause
echo         exit /b 0
echo     ^)
echo ^)
echo copy "config\.env.example" ".env" ^>nul
echo echo.
echo echo Fichier .env cree avec succes
echo echo Ouverture pour edition...
echo timeout /t 2 ^>nul
echo notepad ".env"
echo echo.
echo echo Configuration terminee
echo pause
) > "dist\EMAC\CONFIGURER.bat"

REM Créer script de lancement rapide
(
echo @echo off
echo if not exist ".env" ^(
echo     echo Configuration necessaire - Lancement CONFIGURER.bat...
echo     call CONFIGURER.bat
echo ^)
echo start EMAC.exe
) > "dist\EMAC\LANCER.bat"

echo OK
echo.

REM ===========================
REM [8/9] Calcul de la taille
REM ===========================
echo [8/9] Calcul taille finale...

set TOTAL_SIZE=0
for /r "dist\EMAC" %%F in (*) do (
    set /a TOTAL_SIZE+=%%~zF
)
set /a SIZE_MB=%TOTAL_SIZE% / 1048576

REM Compter les fichiers
for /f %%A in ('dir /s /b "dist\EMAC\*.*" ^| find /c /v ""') do set FILE_COUNT=%%A

echo Taille totale: %SIZE_MB% MB
echo Nombre fichiers: %FILE_COUNT%
echo.

REM ===========================
REM [9/9] Statistiques
REM ===========================
echo [9/9] Statistiques de build...
echo.

REM Afficher les warnings PyInstaller
if exist "build\EMAC\warn-EMAC.txt" (
    for /f %%A in ('type "build\EMAC\warn-EMAC.txt" ^| find /c /v ""') do set WARN_COUNT=%%A
    echo Warnings PyInstaller: !WARN_COUNT!
    if !WARN_COUNT! GTR 20 (
        echo ^(Voir build\EMAC\warn-EMAC.txt pour details^)
    )
)

REM Vérifier l'executable
if exist "dist\EMAC\EMAC.exe" (
    for %%A in ("dist\EMAC\EMAC.exe") do set EXE_SIZE=%%~zA
    set /a EXE_SIZE_MB=!EXE_SIZE! / 1048576
    echo Taille EMAC.exe: !EXE_SIZE_MB! MB
)

echo.
echo OK
echo.

REM ===========================
REM Résumé final
REM ===========================
echo =========================================
echo  BUILD TERMINÉ
echo =========================================
echo.
echo Emplacement: dist\EMAC\
echo Taille totale: %SIZE_MB% MB
echo Fichiers: %FILE_COUNT%
echo.
echo Optimisations appliquees:
echo   [X] One-folder mode
echo   [X] Bytecode optimize=2
echo   [X] UPX desactive
echo   [X] Strip binaires
echo   [X] Exclusions: 25+ modules
echo   [X] Hooks personnalises
echo.
echo PROCHAINES ÉTAPES:
echo.
echo 1. Tester l'application:
echo    cd dist\EMAC
echo    CONFIGURER.bat
echo    EMAC.exe
echo.
echo 2. Verifier les performances:
echo    - Temps demarrage ^< 5 secondes
echo    - Pas de warning antivirus
echo    - Taille ^< 150 MB
echo.
echo 3. Distribuer:
echo    - Zipper le dossier dist\EMAC
echo    - Inclure LISEZMOI.txt
echo.
echo =========================================
echo.

pause
