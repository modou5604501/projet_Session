@echo off
REM ============================================================
REM  GeoCharge Montreal — Script de demarrage (Windows)
REM  Projet : Bornes de recharge electrique - Montreal
REM  Prerequis : Python 3.10+ dans le PATH ou venv actif
REM              (aucune base de donnees, aucun conteneur requis)
REM ============================================================

echo.
echo ============================================================
echo  GeoCharge Montreal - Bornes de recharge Montreal
echo  Demarrage de l'application Shiny...
echo ============================================================
echo.

pip install -r shiny_app\requirements.txt

echo.
echo Lancement du serveur (Ctrl+C pour arreter)...
echo Carte interactive : http://127.0.0.1:8000
echo.

python -m shiny run shiny_app\app.py --reload
