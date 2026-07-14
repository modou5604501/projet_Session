@echo off
setlocal
REM ============================================================
REM  GeoRisk Sentinel — Script de demarrage (Windows)
REM  Projet : Bornes de recharge electrique - Montreal
REM  Prerequis : Docker Desktop en cours d'execution
REM              Python 3.10+ dans le PATH ou venv actif
REM ============================================================

cd /d "%~dp0"

echo.
echo ============================================================
echo  GeoRisk Sentinel - Bornes de recharge Montreal
echo  Demarrage de l'infrastructure...
echo ============================================================
echo.

REM Demarrer PostGIS + pgAdmin
docker-compose up -d postgis pgadmin

if errorlevel 1 (
	echo.
	echo [ERREUR] Impossible de demarrer les services Docker.
	exit /b 1
)

echo.
echo Preparation de l'environnement Python...
if not exist "venv\Scripts\python.exe" (
	echo Creation du venv...
	python -m venv venv
	if errorlevel 1 (
		echo [ERREUR] Echec de creation du venv.
		exit /b 1
	)
)

echo Installation des dependances (requirements.txt)...
"venv\Scripts\python.exe" -m pip install --upgrade pip
"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
	echo [ERREUR] Echec d'installation des dependances Python.
	exit /b 1
)

echo.
echo Attente demarrage PostGIS (15 s)...
timeout /t 15 /nobreak > nul

REM Importer les donnees dans PostGIS
echo.
echo Import des donnees Montreal dans PostGIS...
"venv\Scripts\python.exe" src\preprocessing\import_postgis.py

if errorlevel 1 (
	echo [ERREUR] Echec de l'import des donnees.
	exit /b 1
)

echo.
echo Demarrage du serveur web Django...
echo.
set POSTGRES_PORT=5433
cd src\web
"..\..\venv\Scripts\python.exe" manage.py runserver 0.0.0.0:8000

REM URLs accessibles :
REM   Carte interactive  : http://localhost:8000
REM   API bornes         : http://localhost:8000/api/bornes/
REM   API couverture     : http://localhost:8000/api/couverture/
REM   API arrondissements: http://localhost:8000/api/arrondissements/
REM   API stats          : http://localhost:8000/api/coverage-summary/
REM   Django Admin       : http://localhost:8000/admin/
REM   pgAdmin            : http://localhost:5050
