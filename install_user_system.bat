@echo off
echo ========================================================================
echo INSTALLATION DU SYSTEME DE GESTION DES UTILISATEURS - EMAC
echo ========================================================================
echo.

REM Vérifier que nous sommes dans le bon répertoire
if not exist "App\core\services\auth_service.py" (
    echo ERREUR: Ce script doit etre execute depuis le repertoire racine EMAC
    echo Repertoire actuel: %CD%
    pause
    exit /b 1
)

echo Etape 1/3: Installation des dependances Python...
echo ========================================================================
echo.

pip install bcrypt python-dotenv

if errorlevel 1 (
    echo.
    echo ERREUR: Echec de l'installation des dependances
    pause
    exit /b 1
)

echo.
echo ✓ Dependances installees avec succes
echo.

echo Etape 2/3: Application de la migration de la base de donnees...
echo ========================================================================
echo.

cd App
py scripts\apply_user_management_migration.py

if errorlevel 1 (
    echo.
    echo ERREUR: Echec de la migration
    cd ..
    pause
    exit /b 1
)

cd ..

echo.
echo ✓ Migration appliquee avec succes
echo.

echo Etape 3/3: Test du systeme...
echo ========================================================================
echo.

cd App
py scripts\test_auth_system.py

cd ..

echo.
echo ========================================================================
echo INSTALLATION TERMINEE
echo ========================================================================
echo.
echo Identifiants par defaut:
echo   Username: admin
echo   Password: admin123
echo.
echo ⚠️  IMPORTANT: Changez ce mot de passe des la premiere connexion!
echo.
echo Documentation:
echo   - Guide utilisateur: docs\user\guide-gestion-utilisateurs.md
echo   - Guide technique: docs\dev\authentication-system.md
echo   - README: SYSTEME_UTILISATEURS_README.md
echo.
pause
