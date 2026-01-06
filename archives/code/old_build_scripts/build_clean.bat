@echo off
REM ============================================================================
REM  EMAC - BUILD PROPRE (FICHIERS ESSENTIELS UNIQUEMENT)
REM ============================================================================
REM  Ce script compile l'application en n'incluant QUE les fichiers nécessaires
REM  Référence: BUILD_MANIFEST.txt
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo   EMAC - COMPILATION PROPRE
echo ============================================================================
echo.

REM --- ÉTAPE 1: Vérifications préalables ---
echo [1/6] Verification des prerequis...

if not exist "core\gui\main_qt.py" (
    echo ❌ ERREUR: Fichier core\gui\main_qt.py introuvable
    echo    Assurez-vous d'executer ce script depuis le dossier App/
    pause
    exit /b 1
)

if not exist ".env" (
    echo ⚠️  WARNING: Fichier .env introuvable
    echo    L'application ne pourra pas se connecter a la base de donnees
    echo    Creez un fichier .env avec EMAC_DB_PASSWORD=votre_mot_de_passe
    echo.
    choice /C YN /M "Continuer quand meme"
    if errorlevel 2 exit /b 1
)

if not exist "EMAC_optimized.spec" (
    echo ❌ ERREUR: Fichier EMAC_optimized.spec introuvable
    pause
    exit /b 1
)

echo    ✅ Tous les prerequis sont presents
echo.

REM --- ÉTAPE 2: Nettoyage ---
echo [2/6] Nettoyage des anciens builds...

if exist "build" (
    echo    - Suppression du dossier build/
    rmdir /s /q "build" 2>nul
)

if exist "dist\EMAC" (
    echo    - Suppression du dossier dist\EMAC/
    rmdir /s /q "dist\EMAC" 2>nul
)

REM Nettoyer les fichiers __pycache__ pour réduire la taille
echo    - Nettoyage des __pycache__...
for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul

REM Nettoyer les .pyc
del /s /q *.pyc 2>nul >nul

echo    ✅ Nettoyage termine
echo.

REM --- ÉTAPE 3: Compilation PyInstaller ---
echo [3/6] Compilation avec PyInstaller...
echo    (Ceci peut prendre 2-3 minutes)
echo.

pyinstaller EMAC_optimized.spec --clean --noconfirm

if not exist "dist\EMAC\EMAC.exe" (
    echo.
    echo ❌ ERREUR: La compilation a echoue
    echo    Verifiez les messages d'erreur ci-dessus
    pause
    exit /b 1
)

echo.
echo    ✅ Compilation reussie
echo.

REM --- ÉTAPE 4: Copie des fichiers de configuration ---
echo [4/6] Copie des fichiers de configuration...

REM Copier le .env (CRITIQUE)
if exist ".env" (
    copy /y ".env" "dist\EMAC\.env" >nul 2>&1
    if exist "dist\EMAC\.env" (
        echo    ✅ .env copie
    ) else (
        echo    ❌ Echec copie .env
    )
) else (
    echo    ⚠️  .env non trouve - SKIP
)

REM Copier les fichiers SQL (optionnel)
if exist "database\schema\bddemac.sql" (
    if not exist "dist\EMAC\database\schema" mkdir "dist\EMAC\database\schema"
    copy /y "database\schema\*.sql" "dist\EMAC\database\schema\" >nul 2>&1
    echo    ✅ Schemas SQL copies
)

REM Copier les migrations (optionnel)
if exist "database\migrations" (
    if not exist "dist\EMAC\database\migrations" mkdir "dist\EMAC\database\migrations"
    copy /y "database\migrations\*.sql" "dist\EMAC\database\migrations\" >nul 2>&1
    echo    ✅ Migrations SQL copiees
)

REM Créer les dossiers vides nécessaires
if not exist "dist\EMAC\logs" mkdir "dist\EMAC\logs"
if not exist "dist\EMAC\documents" mkdir "dist\EMAC\documents"
echo    ✅ Dossiers runtime crees (logs, documents)

echo.

REM --- ÉTAPE 5: Nettoyage des fichiers inutiles dans dist ---
echo [5/6] Suppression des fichiers non-essentiels dans dist\EMAC\...

REM Supprimer les tests PyInstaller si présents
if exist "dist\EMAC\tests" (
    rmdir /s /q "dist\EMAC\tests" 2>nul
    echo    - tests/ supprime
)

REM Supprimer les scripts de dev si présents
if exist "dist\EMAC\scripts" (
    rmdir /s /q "dist\EMAC\scripts" 2>nul
    echo    - scripts/ supprime
)

REM Supprimer les fichiers de build PyInstaller
if exist "dist\EMAC\base_library.zip.bak" del /q "dist\EMAC\base_library.zip.bak" 2>nul

echo    ✅ Nettoyage termine
echo.

REM --- ÉTAPE 6: Rapport final ---
echo [6/6] Generation du rapport...
echo.

echo ============================================================================
echo   ✅ BUILD TERMINE AVEC SUCCES
echo ============================================================================
echo.
echo 📂 Emplacement: dist\EMAC\
echo 🚀 Executable:  dist\EMAC\EMAC.exe
echo.

REM Calculer la taille
for /f "tokens=3" %%a in ('dir /s "dist\EMAC" ^| find "octets"') do set SIZE=%%a
echo 📊 Taille totale: %SIZE% octets
echo.

REM Lister les fichiers principaux
echo 📋 Contenu principal:
dir /b "dist\EMAC" | findstr /v "\.pyc$ \.pyd$ \.dll$"
echo.

echo ============================================================================
echo   PROCHAINES ETAPES
echo ============================================================================
echo.
echo 1. ✅ Verifier que dist\EMAC\.env existe et contient votre mot de passe BDD
echo 2. 🧪 Tester: dist\EMAC\EMAC.exe
echo 3. 📦 Deployer: Copier tout le dossier dist\EMAC\ sur le serveur/reseau
echo.
echo ⚠️  IMPORTANT: Copiez TOUT le dossier dist\EMAC\, pas seulement l'EXE!
echo.

REM Vérification finale du .env
if not exist "dist\EMAC\.env" (
    echo ============================================================================
    echo   ⚠️  ATTENTION: .env MANQUANT
    echo ============================================================================
    echo.
    echo Le fichier .env n'a pas ete copie dans dist\EMAC\
    echo L'application NE POURRA PAS demarrer sans ce fichier.
    echo.
    echo Action requise:
    echo   copy .env dist\EMAC\.env
    echo.
    echo ============================================================================
    echo.
)

pause
