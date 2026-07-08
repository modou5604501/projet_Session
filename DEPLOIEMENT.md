# Déploiement sur Railway — GeoRisk Sentinel

## Vue d'ensemble

L'application Django + PostGIS est déployée sur **Railway.app**, une plateforme cloud qui supporte
nativement PostgreSQL/PostGIS. Une fois déployée, l'URL publique permet d'installer l'application
comme **PWA (Progressive Web App)** sur tablette, sans passer par un App Store.

---

## Prérequis

- Compte Railway.app (gratuit) : https://railway.app
- Compte GitHub avec le repo `modou5604501/projet_Session`

---

## Étape 1 — Créer le projet sur Railway

1. Aller sur **https://railway.app** → **New Project**
2. Choisir **Deploy from GitHub repo**
3. Sélectionner `modou5604501/projet_Session`
4. Railway détecte automatiquement `railway.json` et `nixpacks.toml`

---

## Étape 2 — Ajouter la base de données PostgreSQL

1. Dans le projet Railway → **+ Add Service** → **Database** → **PostgreSQL**
2. Railway crée automatiquement la variable `DATABASE_URL`

---

## Étape 3 — Configurer les variables d'environnement

Dans **Settings → Variables**, ajouter :

| Variable | Valeur |
|---|---|
| `DEBUG` | `False` |
| `DJANGO_SECRET_KEY` | Générer une clé aléatoire (ex: `python -c "import secrets; print(secrets.token_hex(50))"`) |
| `ALLOWED_HOSTS` | `*.railway.app` (Railway remplit automatiquement le domaine) |

`DATABASE_URL` est déjà injecté automatiquement par Railway depuis le service PostgreSQL.

---

## Étape 4 — Activer PostGIS

Après le premier déploiement, Railway exécute automatiquement `railway_start.sh` qui active PostGIS :

```bash
python manage.py shell -c "
from django.db import connection
with connection.cursor() as c:
    c.execute('CREATE EXTENSION IF NOT EXISTS postgis;')
"
```

Si l'erreur persiste, le faire manuellement via Railway → PostgreSQL → **Connect** → Query :

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

---

## Étape 5 — Créer les tables et importer les données

1. Dans Railway → ton service Django → **Shell**
2. Exécuter :

```bash
cd src/web
# Créer les tables
python manage.py shell -c "
from django.db import connection
import pathlib
sql = pathlib.Path('../../sql/01_create_tables.sql').read_text()
with connection.cursor() as c:
    c.execute(sql)
print('Tables créées.')
"

# Importer les données (télécharge depuis Données Québec)
python manage.py shell -c "
import sys; sys.path.insert(0, '../../preprocessing')
from refresh_data import run_refresh
r = run_refresh()
print(r)
"
```

---

## Étape 6 — Accéder à l'application

Railway génère une URL publique de la forme :

```
https://projet-session-production.up.railway.app
```

Le dashboard est accessible à cette URL.

---

## Étape 7 — Installer l'application sur tablette (PWA)

### Sur iPad / tablette Android :

1. Ouvrir l'URL Railway dans **Safari (iPad)** ou **Chrome (Android)**
2. Appuyer sur le bouton **Partager** (Safari) ou **⋮** (Chrome)
3. Choisir **"Ajouter à l'écran d'accueil"** / **"Installer l'application"**
4. L'icône GeoRisk Sentinel apparaît sur l'écran d'accueil
5. L'application s'ouvre en plein écran, sans barre de navigation du navigateur

### Fonctionnalités sur tablette :
- Vue plein écran, orientée paysage
- Carte interactive Leaflet (zoom, pan, clic sur entités)
- Informations en temps réel sur les bornes et arrondissements
- Bouton "Mettre à jour" pour re-synchroniser depuis Données Québec

---

## Récapitulatif des variables Railway

```env
DATABASE_URL=postgresql://...  (automatique)
DEBUG=False
DJANGO_SECRET_KEY=<clé-secrete-longue>
ALLOWED_HOSTS=*.railway.app
```

---

## Mise à jour de l'application

Chaque push sur la branche `main` de GitHub déclenche automatiquement un redéploiement Railway.

```bash
git push origin master:main
# Railway redéploie automatiquement en ~2 minutes
```
