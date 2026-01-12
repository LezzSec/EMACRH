@echo off
echo ============================================
echo Nettoyage des caches Python et lancement EMAC
echo ============================================

cd /d "%~dp0"

echo.
echo [1/3] Suppression des fichiers .pyc...
del /s /q *.pyc 2>nul

echo [2/3] Suppression des dossiers __pycache__...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo [3/3] Lancement de l'application...
echo.

python -B -m core.gui.main_qt

echo.
echo Application fermee.
pause
