"""
Django settings for GeoRisk Sentinel
Projet : Optimisation de l'accessibilité aux bornes de recharge électrique à Montréal
"""

import os
from pathlib import Path

# Fix PROJ conflit PostgreSQL local — doit être avant tout import géo
import sys
_proj_data = os.path.join(sys.prefix, "Lib", "site-packages", "rasterio", "proj_data")
if os.path.isdir(_proj_data):
    os.environ.setdefault("PROJ_DATA", _proj_data)
    os.environ.setdefault("PROJ_LIB",  _proj_data)

BASE_DIR = Path(__file__).resolve().parent.parent

# GDAL / GEOS — DLLs bundlées dans le venv (Windows)
# GeoDjango les cherche par nom court (gdal310, geos_c, etc.) ; on pointe
# explicitement vers les DLLs hashées de shapely/rasterio.
import glob as _glob

def _first_dll(patterns):
    for p in patterns:
        hits = _glob.glob(p)
        if hits:
            return hits[0]
    return None

GDAL_LIBRARY_PATH = _first_dll([
    str(Path(sys.prefix) / "Lib/site-packages/rasterio.libs/gdal*.dll"),
    str(Path(sys.prefix) / "Lib/site-packages/fiona.libs/gdal*.dll"),
    r"C:/OSGeo4W/bin/gdal310.dll",
])

GEOS_LIBRARY_PATH = _first_dll([
    str(Path(sys.prefix) / "Lib/site-packages/shapely.libs/geos_c*.dll"),
    str(Path(sys.prefix) / "Lib/site-packages/rasterio.libs/geos_c*.dll"),
    str(Path(sys.prefix) / "Lib/site-packages/fiona.libs/geos_c*.dll"),
    r"C:/OSGeo4W/bin/geos_c.dll",
])
PROJECT_ROOT = BASE_DIR.parent.parent   # GMQ580_projetsession/

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-insecure-georisk-sentinel-2026-change-in-prod"
)

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",           # GeoDjango
    "rest_framework",               # DRF
    "rest_framework_gis",           # GeoJSON serialization
    "corsheaders",                  # CORS
    "risk_map",                     # notre application
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

ROOT_URLCONF = "georisk_web.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "georisk_web.wsgi.application"

# Base de données PostGIS (Docker sur port 5433)
DATABASES = {
    "default": {
        "ENGINE":   "django.contrib.gis.db.backends.postgis",
        "NAME":     os.environ.get("POSTGRES_DB",       "georisk"),
        "USER":     os.environ.get("POSTGRES_USER",     "georisk_user"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "georisk2019"),
        "HOST":     os.environ.get("POSTGRES_HOST",     "localhost"),
        "PORT":     os.environ.get("POSTGRES_PORT",     "5433"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-ca"
TIME_ZONE = "America/Montreal"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

