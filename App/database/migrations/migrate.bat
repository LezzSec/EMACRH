@echo off
chcp 65001 >nul
echo ╔════════════════════════════════════════════════════════════╗
echo ║  MIGRATION EMAC - operateurs → personnel                   ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Vérifier que MySQL est accessible
echo [1/5] Vérification de MySQL...
mysql --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERREUR: MySQL n'est pas installé ou pas dans le PATH
    echo    Installez MySQL ou ajoutez-le au PATH
    pause
    exit /b 1
)
echo ✅ MySQL trouvé
echo.

REM Créer le dossier de backup s'il n'existe pas
if not exist "..\backups" mkdir "..\backups"

REM Demander le mot de passe root
set /p "MYSQL_PASSWORD=Entrez le mot de passe MySQL root: "
echo.

REM Créer un backup
echo [2/5] Création du backup de sécurité...
set BACKUP_FILE=..\backups\backup_avant_migration_%date:~6,4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%.sql
set BACKUP_FILE=%BACKUP_FILE: =0%

mysqldump -u root -p%MYSQL_PASSWORD% emac_db > "%BACKUP_FILE%" 2>nul
if errorlevel 1 (
    echo ❌ ERREUR: Impossible de créer le backup
    echo    Vérifiez le mot de passe et que la base emac_db existe
    pause
    exit /b 1
)
echo ✅ Backup créé: %BACKUP_FILE%
echo.

REM Vérifier l'état actuel
echo [3/5] Vérification de l'état actuel...
mysql -u root -p%MYSQL_PASSWORD% emac_db -e "SELECT COUNT(*) as NombreOperateurs FROM operateurs;" 2>nul
if errorlevel 1 (
    echo ❌ ERREUR: La table operateurs n'existe pas
    echo    Peut-être déjà migrée ?
    pause
    exit /b 1
)
echo ✅ Table operateurs vérifiée
echo.

REM Appliquer la migration
echo [4/5] Application de la migration...
echo ⚠️  ATTENTION: L'application EMAC doit être FERMÉE
set /p "CONFIRM=Confirmez-vous que l'application est fermée ? (O/N): "
if /i not "%CONFIRM%"=="O" (
    echo ❌ Migration annulée
    pause
    exit /b 0
)

mysql -u root -p%MYSQL_PASSWORD% emac_db < migrate_operateurs_to_personnel_safe.sql
if errorlevel 1 (
    echo ❌ ERREUR: La migration a échoué
    echo    Utilisez le backup pour restaurer: %BACKUP_FILE%
    pause
    exit /b 1
)
echo ✅ Migration appliquée avec succès
echo.

REM Vérification finale
echo [5/5] Vérification post-migration...
mysql -u root -p%MYSQL_PASSWORD% emac_db -e "SELECT COUNT(*) as NombrePersonnel FROM personnel;"
if errorlevel 1 (
    echo ❌ ERREUR: Vérification échouée
    pause
    exit /b 1
)
echo ✅ Vérification réussie
echo.

echo ╔════════════════════════════════════════════════════════════╗
echo ║  ✅ MIGRATION TERMINÉE AVEC SUCCÈS !                       ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 📁 Backup sauvegardé dans: %BACKUP_FILE%
echo 🚀 Vous pouvez maintenant relancer l'application EMAC
echo.

pause
