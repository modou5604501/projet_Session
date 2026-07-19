# Exécution et déploiement — GeoCharge Montréal

## Vue d'ensemble

L'application est un **Shiny for Python autonome** (`shiny app/app_bornes_recharges.py`) : aucune base de
données ni conteneur Docker n'est requis. Toutes les couches (`data/vectors/*.geojson`,
`data/demo_arrondissements.csv`) sont chargées et traitées en mémoire avec GeoPandas au démarrage de l'app.

---

## Exécution locale (recommandé pour la soutenance)

### Prérequis
- Python 3.10+
- Le dépôt cloné avec le dossier `data/` intact (toutes les couches sont versionnées sur GitHub)

### Étapes

```bash
git clone https://github.com/modou5604501/projet_Session.git
cd projet_Session

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

pip install -r requirements_bornes_recharges.txt
python -m shiny run --port 8000 "shiny app/app_bornes_recharges.py"
```

Le tableau de bord est accessible sur **http://127.0.0.1:8000**. Le chargement initial (2 412 bornes,
34 arrondissements, 1 541 parcs, 3 010 épiceries + calculs de couverture et jointures spatiales) prend
une quinzaine de secondes.

> `python -m shiny run` est préféré à `shiny run` seul : sur certaines installations (notamment Windows),
> l'exécutable `shiny` n'est pas automatiquement sur le PATH après `pip install`, ce qui provoque une
> erreur `command not found`.

> **Note Windows :** utiliser `python -m shiny run` plutôt que `shiny run` seul — sur certaines
> installations (notamment Windows), l'exécutable `shiny` n'est pas automatiquement sur le PATH après
> `pip install`, ce qui provoque une erreur `command not found`.

---

## Déploiement public (optionnel)

Pour obtenir une URL publique sans gérer de serveur, l'option la plus simple pour une app Shiny for
Python est **[Posit Connect Cloud](https://posit.cloud)** ou **shinyapps.io** :

```bash
pip install rsconnect-python
rsconnect deploy shiny "shiny app/" --name <compte> --title geocharge-montreal
```

Cette étape est optionnelle : pour la soutenance orale, l'exécution locale (ci-dessus) suffit et évite
toute dépendance à un service externe le jour J.

---

## Mise à jour du dépôt

```bash
git add -A
git commit -m "..."
git push origin master
```

Aucun redéploiement automatique n'est configuré (pas d'intégration continue) : si l'app est publiée sur
Posit Connect Cloud / shinyapps.io, il faut relancer manuellement `rsconnect deploy` après chaque changement.
