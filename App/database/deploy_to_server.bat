@echo off
REM ============================================================================
REM Script de déploiement incrémental EMAC vers serveur MySQL
REM ============================================================================
REM Ce script applique les nouvelles tables sans écraser les données existantes
REM ============================================================================

echo ============================================================================
echo EMAC - Déploiement incrémental de la base de données
echo ============================================================================
echo.

REM Vérifier que le fichier SQL existe
if not exist "deploy_incremental.sql" (
    echo ERREUR: Le fichier deploy_incremental.sql est introuvable!
    echo Assurez-vous d'être dans le dossier App\database
    pause
    exit /b 1
)

echo Ce script va déployer les NOUVELLES TABLES uniquement:
echo  - roles
echo  - utilisateurs
echo  - permissions
echo  - logs_connexion
echo  - Colonnes additionnelles dans historique
echo.
echo AUCUNE DONNEE EXISTANTE NE SERA SUPPRIMEE OU ECRASEE
echo.

REM Demander les informations de connexion
set /p DB_HOST="Hôte MySQL (ex: localhost ou IP serveur): "
set /p DB_USER="Utilisateur MySQL (ex: root): "
set /p DB_NAME="Nom de la base de données (ex: emac_db): "
echo.

REM Demander le mot de passe de manière sécurisée
echo Entrez le mot de passe MySQL (il sera masqué):
set "DB_PASSWORD="
call :input_password DB_PASSWORD
echo.

echo ============================================================================
echo Configuration:
echo  - Hôte: %DB_HOST%
echo  - Utilisateur: %DB_USER%
echo  - Base de données: %DB_NAME%
echo ============================================================================
echo.

set /p CONFIRM="Confirmer le déploiement? (O/N): "
if /i not "%CONFIRM%"=="O" (
    echo Déploiement annulé.
    pause
    exit /b 0
)

echo.
echo Déploiement en cours...
echo.

REM Trouver mysql.exe
set "MYSQL_CMD=mysql"

REM Vérifier si mysql est dans le PATH
where mysql >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ATTENTION: mysql n'est pas dans le PATH système
    echo Recherche de MySQL dans les emplacements communs...

    if exist "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" (
        set "MYSQL_CMD=C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
        echo Trouvé: !MYSQL_CMD!
    ) else if exist "C:\xampp\mysql\bin\mysql.exe" (
        set "MYSQL_CMD=C:\xampp\mysql\bin\mysql.exe"
        echo Trouvé: !MYSQL_CMD!
    ) else (
        echo ERREUR: Impossible de trouver mysql.exe
        echo Veuillez ajouter MySQL au PATH ou modifier ce script
        pause
        exit /b 1
    )
)

REM Exécuter le script SQL
"%MYSQL_CMD%" -h %DB_HOST% -u %DB_USER% -p%DB_PASSWORD% %DB_NAME% < deploy_incremental.sql

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================================
    echo SUCCES: Déploiement terminé avec succès!
    echo ============================================================================
    echo.
    echo Les nouvelles tables ont été créées:
    echo  [OK] roles
    echo  [OK] utilisateurs
    echo  [OK] permissions
    echo  [OK] logs_connexion
    echo.
    echo Utilisateur admin créé:
    echo  - Username: admin
    echo  - Mot de passe: admin123
    echo  - IMPORTANT: Changez ce mot de passe dès la première connexion!
    echo.
    echo Vous pouvez maintenant:
    echo  1. Tester la connexion avec l'application
    echo  2. Créer un nouvel EXE avec PyInstaller
    echo.
) else (
    echo.
    echo ============================================================================
    echo ERREUR: Le déploiement a échoué!
    echo ============================================================================
    echo Vérifiez:
    echo  1. Les informations de connexion (hôte, utilisateur, mot de passe)
    echo  2. Que la base de données '%DB_NAME%' existe
    echo  3. Que l'utilisateur a les droits CREATE TABLE et INSERT
    echo.
)

pause
exit /b %ERRORLEVEL%

REM ============================================================================
REM Fonction pour saisir un mot de passe masqué (Windows)
REM ============================================================================
:input_password
setlocal enabledelayedexpansion
set "psCommand=powershell -Command "$pword = read-host -AsSecureString ; ^
    $BSTR=[System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($pword); ^
    [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)""
for /f "usebackq delims=" %%p in (`%psCommand%`) do set "password=%%p"
endlocal & set "%~1=%password%"
goto :eof
