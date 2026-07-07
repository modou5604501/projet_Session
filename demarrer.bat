@echo off
REM ============================================================
REM  GeoRisk Sentinel — Script de démarrage (Windows)
REM  Lance PostGIS + pgAdmin + Django en un clic
REM  Prérequis : Docker Desktop en cours d'exécution
REM ============================================================

echo.
echo ============================================================
echo  GeoRisk Sentinel — Sainte-Marthe-sur-le-Lac
echo  Demarrage de l'infrastructure...
echo ============================================================
echo.

REM Démarrer les services Docker
docker-compose up -d postgis pgadmin

echo.
echo Attente demarrage PostGIS (10 s)...
timeout /t 10 /nobreak > nul

REM Lancer Django en local (avec les variables d'environnement)
set PROJ_LIB=C:\Users\KHABA\venv\Lib\site-packages\rasterio\proj_data
set PROJ_DATA=C:\Users\KHABA\venv\Lib\site-packages\rasterio\proj_data
set POSTGRES_PORT=5433

echo.
echo Demarrage du serveur web Django...
echo.
cd src\web
C:\Users\KHABA\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000

REM URLs utiles :
REM   Carte : http://localhost:8000
REM   API   : http://localhost:8000/api/
REM   Admin : http://localhost:8000/admin/
REM   pgAdmin : http://localhost:5050
