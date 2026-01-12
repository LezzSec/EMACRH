@echo off
echo ============================================================
echo LANCEMENT DE L'APPLICATION AVEC LOGS DEBUG
echo ============================================================
echo.
echo IMPORTANT: Laissez cette fenetre ouverte pour voir les logs
echo.

cd /d "%~dp0\App"

echo Chargement de l'application...
echo.

python -m core.gui.main_qt

echo.
echo ============================================================
echo Application fermee
echo ============================================================
echo.
pause
