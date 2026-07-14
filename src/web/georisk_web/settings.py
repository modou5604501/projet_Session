"""
Django settings for GeoCharge Montréal
Projet : Optimisation de l'accessibilité aux bornes de recharge électrique à Montréal
"""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent.parent   # GMQ580_projetsession/

# ── GDAL/GEOS : Windows uniquement (Linux = bibliothèques système) ──
if sys.platform == "win32":
    import glob as _glob

    def _first_dll(patterns):
        for p in patterns:
            hits = _glob.glob(p)
            if hits:
                return hits[0]
        return None

    # Fix PROJ avant tout import géo (pyproj ou fiona comme source de vérité)
    try:
        from pyproj.datadir import get_data_dir as _get_pyproj_dir
        _proj_data = _get_pyproj_dir()
        os.environ.setdefault("PROJ_DATA", _proj_data)
        os.environ.setdefault("PROJ_LIB",  _proj_data)
    except Exception:
        pass

    GDAL_LIBRARY_PATH = _first_dll([
        str(Path(sys.prefix) / "Lib/site-packages/fiona.libs/gdal*.dll"),
        r"C:/OSGeo4W/bin/gdal310.dll",
        r"C:/Program Files/QGIS 3.34.6/bin/gdal308.dll",
        r"C:/Program Files/QGIS 3.34.6/bin/gdal*.dll",
    ])
    GEOS_LIBRARY_PATH = _first_dll([
        str(Path(sys.prefix) / "Lib/site-packages/shapely.libs/geos_c*.dll"),
        str(Path(sys.prefix) / "Lib/site-packages/fiona.libs/geos_c*.dll"),
        r"C:/OSGeo4W/bin/geos_c.dll",
        r"C:/Program Files/QGIS 3.34.6/bin/geos_c.dll",
    ])
else:
    # Linux/Railway : laisser Django trouver les libs système
    # Surcharger via env si nécessaire
    if os.environ.get("GDAL_LIBRARY_PATH"):
        GDAL_LIBRARY_PATH = os.environ["GDAL_LIBRARY_PATH"]
    if os.environ.get("GEOS_LIBRARY_PATH"):
        GEOS_LIBRARY_PATH = os.environ["GEOS_LIBRARY_PATH"]

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-insecure-georisk-sentinel-2026-change-in-prod"
)

DEBUG = os.environ.get("DEBUG", "True") == "True"

_extra_hosts = os.environ.get("ALLOWED_HOSTS", "").split(",")
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"] + [h for h in _extra_hosts if h]

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
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
CORS_ALLOW_ALL_ORIGINS = not DEBUG

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

# Base de données PostGIS
# Railway fournit DATABASE_URL, sinon on utilise les variables locales
if os.environ.get("DATABASE_URL"):
    _u = urlparse(os.environ["DATABASE_URL"])
    DATABASES = {
        "default": {
            "ENGINE":   "django.contrib.gis.db.backends.postgis",
            "NAME":     _u.path.lstrip("/"),
            "USER":     _u.username,
            "PASSWORD": _u.password,
            "HOST":     _u.hostname,
            "PORT":     _u.port or 5432,
        }
    }
else:
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
# En développement, Django sert les fichiers statiques directement (pas de collectstatic).
# En production (Railway), Whitenoise compresse mais ne renomme PAS les fichiers :
# CompressedStaticFilesStorage (pas Manifest) pour garder les URLs stables
# (sw.js, manifest.json, icônes référencés hardcodés dans map.html et manifest.json).
if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

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

