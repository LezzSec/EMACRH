@echo off
REM ============================================================================
REM build_final.bat - Compilation EMAC version finale (RELEASE)
REM ============================================================================
REM Version optimisee avec fichier .env CHIFFRE pour distribution securisee
REM ============================================================================

echo.
echo ================================================================================
echo EMAC - Build FINAL (version release avec .env chiffre)
echo ================================================================================
echo.

REM Verifier qu'on est dans le bon dossier
if not exist "EMAC.spec" (
    echo [ERREUR] Fichier EMAC.spec introuvable.
    pause
    exit /b 1
)

REM Verifier que le fichier .env existe
if not exist "App\.env" (
    echo [ERREUR] Fichier App\.env introuvable.
    echo          Creez d'abord le fichier .env avec vos parametres DB.
    pause
    exit /b 1
)

echo [1/6] Nettoyage des anciens builds...
if exist "build" rmdir /S /Q "build"
if exist "dist" rmdir /S /Q "dist"
if exist "App\.env.encrypted" del /Q "App\.env.encrypted"
echo       OK
echo.

echo [2/6] Chiffrement du fichier .env...
echo       Utilisation de Fernet (AES-128-CBC)
python -c "import sys; sys.path.insert(0, 'App'); from core.utils.config_crypter import encrypt_env_file; encrypt_env_file('App/.env', 'App/.env.encrypted')"
if errorlevel 1 (
    echo.
    echo [ERREUR] Le chiffrement a echoue.
    echo          Verifiez que cryptography est installe: pip install cryptography
    pause
    exit /b 1
)
echo.

echo [3/6] Compilation avec PyInstaller (mode release)...
echo       Configuration: console=False, strip=True, optimize=2
echo       Duree estimee: 2-3 minutes
echo.
pyinstaller EMAC.spec
if errorlevel 1 (
    echo.
    echo [ERREUR] La compilation a echoue.
    pause
    exit /b 1
)
echo       OK
echo.

echo [4/6] Verification de l'executable...
if not exist "dist\EMAC\EMAC.exe" (
    echo [ERREUR] L'executable n'a pas ete cree.
    pause
    exit /b 1
)
echo       OK
echo.

echo [5/6] Copie du fichier .env.encrypted dans _internal...
if exist "App\.env.encrypted" (
    REM PyInstaller met les fichiers data dans _internal/
    if not exist "dist\EMAC\_internal" mkdir "dist\EMAC\_internal"
    copy /Y "App\.env.encrypted" "dist\EMAC\_internal\.env.encrypted" >nul
    echo       OK - Fichier chiffre copie dans _internal/
    REM Supprimer le fichier temporaire chiffre
    del /Q "App\.env.encrypted"
) else (
    echo [ERREUR] Fichier App\.env.encrypted introuvable.
    pause
    exit /b 1
)
echo.

echo [6/6] Creation du README pour distribution...
(
echo EMAC - Application de Gestion du Personnel
echo ===========================================
echo.
echo Installation:
echo   1. Copiez tout le dossier EMAC sur votre ordinateur
echo   2. Lancez EMAC.exe
echo.
echo NOTE: La configuration de base de donnees est integree de maniere
echo       securisee dans l'application (fichier chiffre).
echo.
echo Configuration requise:
echo   - Windows 10/11
echo   - MySQL 8.0 ou superieur
echo   - Connexion reseau a la base de donnees
echo.
echo Support:
echo   Consultez la documentation dans le dossier docs/
echo.
) > "dist\EMAC\README.txt"
echo       OK
echo.

echo ================================================================================
echo BUILD FINAL TERMINE AVEC SUCCES
echo ================================================================================
echo.
echo Fichier genere: dist\EMAC\EMAC.exe
echo.
echo Caracteristiques:
echo   - Mode GUI pur (pas de console)
echo   - Bytecode Python optimise
echo   - Symboles de debug supprimes
echo   - Configuration DB CHIFFREE (AES-128)
echo   - Pret pour la distribution SECURISEE
echo.
echo ================================================================================
echo SECURITE
echo ================================================================================
echo.
echo Le fichier .env a ete chiffre avec Fernet (AES-128-CBC).
echo Les identifiants DB sont proteges et integres dans l'executable.
echo Le fichier .env original n'est PAS inclus dans la distribution.
echo.
echo ================================================================================
echo DISTRIBUTION
echo ================================================================================
echo.
echo Pour distribuer l'application:
echo   1. Compressez le dossier dist\EMAC\ en ZIP
echo   2. Distribuez l'archive ZIP
echo   3. L'utilisateur decompresse et lance EMAC.exe
echo      (aucune configuration necessaire!)
echo.
echo IMPORTANT: Tous les fichiers du dossier sont requis.
echo ================================================================================
echo.

pause
