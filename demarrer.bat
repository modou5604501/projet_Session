@echo off
REM ============================================================
REM  GeoRisk Sentinel — Script de demarrage (Windows)
REM  Projet : Bornes de recharge electrique - Montreal
REM  Prerequis : Docker Desktop en cours d'execution
REM              Python 3.10+ dans le PATH ou venv actif
REM ============================================================

echo.
echo ============================================================
echo  GeoRisk Sentinel - Bornes de recharge Montreal
echo  Demarrage de l'infrastructure...
echo ============================================================
echo.

REM Demarrer PostGIS + pgAdmin
docker-compose up -d postgis pgadmin

echo.
echo Attente demarrage PostGIS (15 s)...
timeout /t 15 /nobreak > nul

REM Importer les donnees dans PostGIS
echo.
echo Import des donnees Montreal dans PostGIS...
python src\preprocessing\import_postgis.py

echo.
echo Analyse de couverture (buffer 500m + statistiques)...
python src\preprocessing\buffer_analysis.py

echo.
echo Demarrage du serveur web Django...
echo.
set POSTGRES_PORT=5433
cd src\web
python manage.py runserver 0.0.0.0:8000

REM URLs accessibles :
REM   Carte interactive  : http://localhost:8000
REM   API bornes         : http://localhost:8000/api/bornes/
REM   API couverture     : http://localhost:8000/api/couverture/
REM   API arrondissements: http://localhost:8000/api/arrondissements/
REM   API stats          : http://localhost:8000/api/coverage-summary/
REM   Django Admin       : http://localhost:8000/admin/
REM   pgAdmin            : http://localhost:5050
