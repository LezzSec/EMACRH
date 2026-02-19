@echo off
chcp 65001 >nul
title EMAC - Tests

echo.
echo ============================================================
echo   EMAC - Lancement des tests
echo ============================================================
echo.

cd /d "%~dp0App"

REM Vérifier que Python est disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH.
    pause
    exit /b 1
)

REM Vérifier que pytest est disponible
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] pytest n'est pas installe. Lancez : pip install pytest
    pause
    exit /b 1
)

echo  Options disponibles :
echo   1. Tests unitaires uniquement  (rapide, sans DB)
echo   2. Tous les tests             (unitaires + integration, necessite DB)
echo   3. Tests avec rapport detaille
echo   4. Tests avec couverture de code
echo.
set /p choix="Votre choix [1-4, Entree=1] : "
if "%choix%"=="" set choix=1

echo.
echo ============================================================

if "%choix%"=="1" (
    echo  Lancement des tests UNITAIRES...
    echo ============================================================
    python -m pytest tests/unit/ -v --tb=short --color=yes
)

if "%choix%"=="2" (
    echo  Lancement de TOUS les tests...
    echo ============================================================
    python -m pytest tests/ -v --tb=short --color=yes
)

if "%choix%"=="3" (
    echo  Lancement avec rapport detaille...
    echo ============================================================
    python -m pytest tests/unit/ -v --tb=long --color=yes -s
)

if "%choix%"=="4" (
    echo  Lancement avec couverture de code...
    echo ============================================================
    python -m pytest tests/unit/ -v --tb=short --color=yes --cov=core --cov-report=term-missing --cov-report=html
    echo.
    echo Rapport HTML genere dans : App\htmlcov\index.html
)

echo.
echo ============================================================
if errorlevel 0 (
    echo  Tous les tests sont passes !
) else (
    echo  Certains tests ont echoue. Voir les details ci-dessus.
)
echo ============================================================
echo.
pause
