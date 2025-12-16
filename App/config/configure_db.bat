@echo off
chcp 65001 > nul
echo ============================================
echo   Configuration Base de Données EMAC
echo ============================================
echo.

REM Vérifier si le fichier .env existe déjà
if exist ".env" (
    echo [INFO] Le fichier .env existe déjà.
    echo.
    choice /C ON /M "Voulez-vous le remplacer"
    if errorlevel 2 (
        echo Configuration annulée.
        pause
        exit /b
    )
)

REM Copier le template
if not exist ".env.example" (
    echo [ERREUR] Le fichier .env.example est introuvable !
    pause
    exit /b 1
)

copy ".env.example" ".env" > nul

echo.
echo [OK] Fichier .env créé avec succès !
echo.
echo ============================================
echo   Configuration du mot de passe MySQL
echo ============================================
echo.
set /p db_password="Entrez le mot de passe MySQL (défaut: emacViodos$13): "

if "%db_password%"=="" (
    set db_password=emacViodos$13
)

echo.
set /p db_host="Entrez l'hôte MySQL (défaut: localhost): "
if "%db_host%"=="" (
    set db_host=localhost
)

set /p db_user="Entrez l'utilisateur MySQL (défaut: root): "
if "%db_user%"=="" (
    set db_user=root
)

set /p db_name="Entrez le nom de la base (défaut: emac_db): "
if "%db_name%"=="" (
    set db_name=emac_db
)

set /p db_port="Entrez le port MySQL (défaut: 3306): "
if "%db_port%"=="" (
    set db_port=3306
)

REM Écrire la configuration dans .env
(
echo # Configuration de la base de données EMAC
echo EMAC_DB_PASSWORD=%db_password%
echo EMAC_DB_HOST=%db_host%
echo EMAC_DB_USER=%db_user%
echo EMAC_DB_NAME=%db_name%
echo EMAC_DB_PORT=%db_port%
) > .env

echo.
echo ============================================
echo   Configuration terminée !
echo ============================================
echo.
echo Fichier .env créé avec les paramètres :
echo   - Hôte      : %db_host%
echo   - Utilisateur : %db_user%
echo   - Base      : %db_name%
echo   - Port      : %db_port%
echo.
echo [SÉCURITÉ] Le mot de passe est stocké dans .env
echo            Ce fichier est ignoré par Git et ne sera pas commité.
echo.

REM Tester la connexion
echo Test de la connexion à la base de données...
py -c "from core.db.configbd import get_connection; conn = get_connection(); print('Connexion MySQL reussie !'); conn.close()" 2>nul

if errorlevel 1 (
    echo.
    echo [ERREUR] Impossible de se connecter à MySQL !
    echo Vérifiez les paramètres dans le fichier .env
) else (
    echo.
    echo [OK] Connexion MySQL réussie !
)

echo.
pause
