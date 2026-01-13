@echo off
REM ============================================================================
REM build_release.bat - Compilation EMAC version finale
REM ============================================================================
REM Ce script compile l'application en mode release (sans console)
REM A N'UTILISER QUE si la version debug fonctionne correctement
REM
REM Usage:
REM   build_release.bat
REM
REM Output:
REM   dist/EMAC/EMAC.exe (version finale optimisée)
REM ============================================================================

echo.
echo ================================================================================
echo EMAC - Build Release (version finale)
echo ================================================================================
echo.

REM Vérifier qu'on est dans le bon dossier
if not exist "EMAC.spec" (
    echo [ERREUR] Fichier EMAC.spec introuvable.
    echo Vous devez executer ce script depuis le dossier racine du projet.
    pause
    exit /b 1
)

echo [AVERTISSEMENT] Cette compilation va creer une version SANS console.
echo                 Si l'application crash, vous ne verrez pas les erreurs.
echo.
echo                 Utilisez build_debug.bat pour le debug.
echo.
set /p "confirm=Continuer la compilation en mode release ? (O/N): "
if /i not "%confirm%"=="O" (
    echo Compilation annulee.
    pause
    exit /b 0
)
echo.

echo [INFO] Verification du fichier EMAC.spec...
findstr /C:"console=True" EMAC.spec >nul
if not errorlevel 1 (
    echo.
    echo [ERREUR] Le fichier EMAC.spec est encore en mode debug ^(console=True^).
    echo.
    echo Vous devez modifier EMAC.spec:
    echo   - Ligne ~254: console=True  -^> console=False
    echo   - Ligne ~252: strip=False   -^> strip=True
    echo.
    echo Puis relancer ce script.
    pause
    exit /b 1
)
echo       OK - Mode release detecte
echo.

echo [1/5] Nettoyage des anciens builds...
if exist "build" rmdir /S /Q "build"
if exist "dist" rmdir /S /Q "dist"
echo       OK - Dossiers build et dist supprimes
echo.

echo [2/5] Compilation avec PyInstaller (mode release)...
echo       Fichier: EMAC.spec
echo       Mode: one-folder, console=False, strip=True
echo       Duree estimee: 2-3 minutes
echo.
pyinstaller EMAC.spec
if errorlevel 1 (
    echo.
    echo [ERREUR] La compilation a echoue.
    echo Verifiez les erreurs ci-dessus.
    pause
    exit /b 1
)
echo       OK - Compilation terminee
echo.

echo [3/5] Verification de l'executable...
if not exist "dist\EMAC\EMAC.exe" (
    echo [ERREUR] L'executable n'a pas ete cree.
    echo Verifiez les erreurs de compilation.
    pause
    exit /b 1
)
echo       OK - EMAC.exe trouve
echo.

echo [4/5] Copie du fichier .env (configuration DB)...
if exist "App\.env" (
    copy /Y "App\.env" "dist\EMAC\.env" >nul
    echo       OK - .env copie
) else (
    echo [ERREUR] Fichier App\.env introuvable.
    echo          L'application ne pourra pas se connecter a la base de donnees.
    echo          Creez App\.env avec vos parametres de connexion DB.
    pause
    exit /b 1
)
echo.

echo [5/5] Calcul de la taille du build...
for /f "tokens=3" %%a in ('dir /s "dist\EMAC" ^| findstr "octets"') do set size=%%a
echo       Taille totale: %size% octets
echo.

echo ================================================================================
echo BUILD RELEASE TERMINE AVEC SUCCES
echo ================================================================================
echo.
echo Fichiers generes:
echo   - dist\EMAC\EMAC.exe           (executable optimise, sans console)
echo   - dist\EMAC\.env               (configuration DB)
echo   - dist\EMAC\*.dll              (dependances)
echo.
echo Caracteristiques:
echo   - Mode GUI pur (pas de console)
echo   - Bytecode Python optimise (optimize=2)
echo   - Symboles de debug supprimes (strip=True)
echo   - Pret pour la distribution
echo.
echo ================================================================================
echo DISTRIBUTION
echo ================================================================================
echo.
echo Pour distribuer l'application:
echo.
echo 1. Copiez tout le dossier dist\EMAC\ (pas juste l'exe)
echo 2. Assurez-vous que .env est present avec les bons parametres DB
echo 3. L'utilisateur peut lancer EMAC.exe directement
echo.
echo NOTE: Tous les fichiers dans dist\EMAC\ sont requis.
echo       Ne distribuez pas uniquement EMAC.exe.
echo.
echo ================================================================================
echo.

echo Lancer l'application maintenant ? (O/N)
set /p "launch=Choix: "
if /i "%launch%"=="O" (
    echo Lancement de EMAC...
    start "" "dist\EMAC\EMAC.exe"
)

pause
