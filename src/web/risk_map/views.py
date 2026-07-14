import json
import sys
import os
import threading
from django.conf import settings
from django.db import connection
from django.http import FileResponse, Http404
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import BorneRecharge, ZoneCouverture, Arrondissement, StationMetro, Parc, Epicerie
from .serializers import (
    BorneRechargeSerializer,
    ZoneCouvertureSerializer,
    ArrondissementSerializer,
    StationMetroSerializer,
    ParcSerializer,
    EpicerieSerializer,
)

# Données socio-démographiques par arrondissement — StatCan Recensement 2021
# Sources : Commande personnalisée recensement 2021, Données Québec / Ville de Montréal
# pop_2021 : population totale
# densite_pop : habitants/km²
# revenu_median : revenu médian des ménages ($)
# tx_propriete : % ménages propriétaires
# tx_voiture : % ménages avec au moins un véhicule (proxy pour demande EV)
# tx_faible_revenu : % population sous seuil de faible revenu (MBM 2021)
_DEMO_DATA = {
    "Ahuntsic-Cartierville": {
        "pop_2021": 141_560, "densite_pop": 5_200,
        "revenu_median": 62_000, "tx_propriete": 35, "tx_voiture": 70, "tx_faible_revenu": 17
    },
    "Anjou": {
        "pop_2021": 43_105, "densite_pop": 3_100,
        "revenu_median": 62_000, "tx_propriete": 55, "tx_voiture": 82, "tx_faible_revenu": 12
    },
    "Côte-des-Neiges–Notre-Dame-de-Grâce": {
        "pop_2021": 173_145, "densite_pop": 8_100,
        "revenu_median": 53_000, "tx_propriete": 28, "tx_voiture": 55, "tx_faible_revenu": 25
    },
    "Côte-des-Neiges-Notre-Dame-de-Grâce": {
        "pop_2021": 173_145, "densite_pop": 8_100,
        "revenu_median": 53_000, "tx_propriete": 28, "tx_voiture": 55, "tx_faible_revenu": 25
    },
    "Lachine": {
        "pop_2021": 47_370, "densite_pop": 2_700,
        "revenu_median": 55_000, "tx_propriete": 45, "tx_voiture": 75, "tx_faible_revenu": 16
    },
    "LaSalle": {
        "pop_2021": 80_615, "densite_pop": 4_400,
        "revenu_median": 57_000, "tx_propriete": 48, "tx_voiture": 78, "tx_faible_revenu": 14
    },
    "Le Plateau-Mont-Royal": {
        "pop_2021": 105_520, "densite_pop": 14_800,
        "revenu_median": 70_000, "tx_propriete": 18, "tx_voiture": 38, "tx_faible_revenu": 13
    },
    "Plateau-Mont-Royal": {
        "pop_2021": 105_520, "densite_pop": 14_800,
        "revenu_median": 70_000, "tx_propriete": 18, "tx_voiture": 38, "tx_faible_revenu": 13
    },
    "Le Sud-Ouest": {
        "pop_2021": 79_815, "densite_pop": 7_600,
        "revenu_median": 58_000, "tx_propriete": 25, "tx_voiture": 52, "tx_faible_revenu": 18
    },
    "Sud-Ouest": {
        "pop_2021": 79_815, "densite_pop": 7_600,
        "revenu_median": 58_000, "tx_propriete": 25, "tx_voiture": 52, "tx_faible_revenu": 18
    },
    "L'Île-Bizard–Sainte-Geneviève": {
        "pop_2021": 20_990, "densite_pop": 520,
        "revenu_median": 82_000, "tx_propriete": 78, "tx_voiture": 94, "tx_faible_revenu": 5
    },
    "Île-Bizard-Sainte-Geneviève": {
        "pop_2021": 20_990, "densite_pop": 520,
        "revenu_median": 82_000, "tx_propriete": 78, "tx_voiture": 94, "tx_faible_revenu": 5
    },
    "Mercier–Hochelaga-Maisonneuve": {
        "pop_2021": 131_460, "densite_pop": 6_900,
        "revenu_median": 50_000, "tx_propriete": 32, "tx_voiture": 62, "tx_faible_revenu": 22
    },
    "Mercier-Hochelaga-Maisonneuve": {
        "pop_2021": 131_460, "densite_pop": 6_900,
        "revenu_median": 50_000, "tx_propriete": 32, "tx_voiture": 62, "tx_faible_revenu": 22
    },
    "Montréal-Nord": {
        "pop_2021": 83_868, "densite_pop": 10_200,
        "revenu_median": 37_000, "tx_propriete": 22, "tx_voiture": 60, "tx_faible_revenu": 38
    },
    "Outremont": {
        "pop_2021": 24_215, "densite_pop": 6_500,
        "revenu_median": 90_000, "tx_propriete": 42, "tx_voiture": 65, "tx_faible_revenu": 8
    },
    "Pierrefonds-Roxboro": {
        "pop_2021": 70_250, "densite_pop": 2_400,
        "revenu_median": 72_000, "tx_propriete": 68, "tx_voiture": 88, "tx_faible_revenu": 8
    },
    "Rivière-des-Prairies–Pointe-aux-Trembles": {
        "pop_2021": 107_170, "densite_pop": 2_900,
        "revenu_median": 53_000, "tx_propriete": 52, "tx_voiture": 80, "tx_faible_revenu": 16
    },
    "Rivière-des-Prairies-Pointe-aux-Trembles": {
        "pop_2021": 107_170, "densite_pop": 2_900,
        "revenu_median": 53_000, "tx_propriete": 52, "tx_voiture": 80, "tx_faible_revenu": 16
    },
    "Rosemont–La Petite-Patrie": {
        "pop_2021": 143_635, "densite_pop": 9_300,
        "revenu_median": 65_000, "tx_propriete": 28, "tx_voiture": 55, "tx_faible_revenu": 14
    },
    "Rosemont-La Petite-Patrie": {
        "pop_2021": 143_635, "densite_pop": 9_300,
        "revenu_median": 65_000, "tx_propriete": 28, "tx_voiture": 55, "tx_faible_revenu": 14
    },
    "Saint-Laurent": {
        "pop_2021": 101_735, "densite_pop": 2_800,
        "revenu_median": 60_000, "tx_propriete": 42, "tx_voiture": 80, "tx_faible_revenu": 15
    },
    "Saint-Léonard": {
        "pop_2021": 73_490, "densite_pop": 7_200,
        "revenu_median": 55_000, "tx_propriete": 50, "tx_voiture": 78, "tx_faible_revenu": 16
    },
    "Verdun": {
        "pop_2021": 69_795, "densite_pop": 9_100,
        "revenu_median": 62_000, "tx_propriete": 30, "tx_voiture": 55, "tx_faible_revenu": 14
    },
    "Ville-Marie": {
        "pop_2021": 84_885, "densite_pop": 10_500,
        "revenu_median": 65_000, "tx_propriete": 20, "tx_voiture": 40, "tx_faible_revenu": 19
    },
    "Villeray–Saint-Michel–Parc-Extension": {
        "pop_2021": 149_490, "densite_pop": 9_800,
        "revenu_median": 48_000, "tx_propriete": 22, "tx_voiture": 58, "tx_faible_revenu": 28
    },
    "Villeray-Saint-Michel-Parc Extension": {
        "pop_2021": 149_490, "densite_pop": 9_800,
        "revenu_median": 48_000, "tx_propriete": 22, "tx_voiture": 58, "tx_faible_revenu": 28
    },
    "Villeray-Saint-Michel-Parc-Extension": {
        "pop_2021": 149_490, "densite_pop": 9_800,
        "revenu_median": 48_000, "tx_propriete": 22, "tx_voiture": 58, "tx_faible_revenu": 28
    },
}
# Alias rétrocompatible pour l'analyse d'équité (revenu seul)
_INCOME_DATA = {k: v["revenu_median"] for k, v in _DEMO_DATA.items()}

_gaps_cache = None

PREPROCESSING_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "preprocessing")
)
if PREPROCESSING_DIR not in sys.path:
    sys.path.insert(0, PREPROCESSING_DIR)


def map_view(request):
    return render(request, "risk_map/map.html")


def serve_sw(request):
    """Sert le service worker depuis /sw.js avec scope racine (PWA)."""
    # Prod : collectstatic a copié le fichier dans STATIC_ROOT
    sw_path = os.path.join(settings.STATIC_ROOT, "risk_map", "sw.js")
    if not os.path.exists(sw_path):
        # Dev : chercher dans le répertoire statique de l'app
        sw_path = os.path.join(os.path.dirname(__file__), "static", "risk_map", "sw.js")
    if not os.path.exists(sw_path):
        raise Http404("Service worker introuvable")
    response = FileResponse(open(sw_path, "rb"), content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    return response


class BorneRechargeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = BorneRecharge.objects.all()
    serializer_class = BorneRechargeSerializer


class ZoneCouvertureViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = ZoneCouverture.objects.all()
    serializer_class = ZoneCouvertureSerializer


class ArrondissementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = Arrondissement.objects.all()
    serializer_class = ArrondissementSerializer


class StationMetroViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = StationMetro.objects.all()
    serializer_class = StationMetroSerializer


class ParcViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = Parc.objects.all()
    serializer_class = ParcSerializer


class EpicerieViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = Epicerie.objects.all()
    serializer_class = EpicerieSerializer


@api_view(["GET"])
def coverage_summary(request):
    """Résumé de couverture par arrondissement."""
    arrondissements = list(Arrondissement.objects.all().values(
        "nom", "nb_bornes", "pct_couverture"
    ).order_by("pct_couverture"))

    total_bornes = BorneRecharge.objects.count()
    sous_desservis = sum(1 for a in arrondissements if a["pct_couverture"] < 30)

    return Response({
        "total_bornes":          total_bornes,
        "total_arrondissements": Arrondissement.objects.count(),
        "sous_desservis":        sous_desservis,
        "arrondissements":       arrondissements,
    })


_refresh_lock = threading.Lock()
_refresh_status = {"running": False, "last_result": None}


@api_view(["POST"])
def trigger_refresh(request):
    """Déclenche manuellement la mise à jour des données depuis Données Québec."""
    global _refresh_status

    if _refresh_status["running"]:
        return Response({"status": "en cours", "message": "Mise à jour déjà en cours..."})

    def _run():
        global _refresh_status
        _refresh_status["running"] = True
        try:
            from refresh_data import run_refresh
            result = run_refresh()
            _refresh_status["last_result"] = result
        except Exception as e:
            _refresh_status["last_result"] = {"status": "error", "message": str(e)}
        finally:
            _refresh_status["running"] = False

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return Response({"status": "démarré", "message": "Mise à jour en cours... Rechargez la carte dans 30 secondes."})


@api_view(["GET"])
def refresh_status(request):
    """Retourne l'état de la dernière mise à jour."""
    return Response({
        "running":     _refresh_status["running"],
        "last_result": _refresh_status["last_result"],
    })


# ── REQUÊTES SPATIALES ──────────────────────────────────────────────────────

@api_view(["GET"])
def query_bornes_proches(request):
    """N bornes les plus proches d'un point (KNN PostGIS <-> operator)."""
    try:
        lat = float(request.GET["lat"])
        lng = float(request.GET["lng"])
        n   = min(int(request.GET.get("n", 5)), 20)
    except (KeyError, ValueError, TypeError):
        return Response({"error": "Paramètres lat, lng requis."}, status=400)

    with connection.cursor() as cur:
        cur.execute("""
            SELECT id, nom, type, arrondissement, nb_prises,
                   ROUND(ST_Distance(
                       geom::geography,
                       ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                   )) AS distance_m,
                   ST_X(geom) AS lng, ST_Y(geom) AS lat
            FROM bornes_recharge
            ORDER BY geom::geography <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
            LIMIT %s
        """, [lng, lat, lng, lat, n])
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    return Response({"bornes": rows, "count": len(rows),
                     "point": {"lat": lat, "lng": lng}, "n": n})


@api_view(["GET"])
def query_bornes_rayon(request):
    """Bornes dans un rayon R autour d'un point (ST_DWithin sur géographie)."""
    try:
        lat   = float(request.GET["lat"])
        lng   = float(request.GET["lng"])
        rayon = min(int(request.GET.get("rayon", 500)), 5000)
    except (KeyError, ValueError, TypeError):
        return Response({"error": "Paramètres lat, lng requis."}, status=400)

    with connection.cursor() as cur:
        cur.execute("""
            SELECT id, nom, type, arrondissement, nb_prises,
                   ROUND(ST_Distance(
                       geom::geography,
                       ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                   )) AS distance_m,
                   ST_X(geom) AS lng, ST_Y(geom) AS lat
            FROM bornes_recharge
            WHERE ST_DWithin(
                geom::geography,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s
            )
            ORDER BY distance_m
        """, [lng, lat, lng, lat, rayon])
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    return Response({"bornes": rows, "count": len(rows),
                     "point": {"lat": lat, "lng": lng}, "rayon_m": rayon})


@api_view(["GET"])
def query_metro_sans_borne(request):
    """Stations de métro sans borne dans un rayon R (NOT EXISTS + ST_DWithin)."""
    rayon = min(int(request.GET.get("rayon", 500)), 2000)

    with connection.cursor() as cur:
        cur.execute("""
            SELECT m.id, m.nom, m.ligne,
                   ST_X(m.geom) AS lng, ST_Y(m.geom) AS lat,
                   ROUND(
                       (SELECT MIN(ST_Distance(m.geom::geography, b.geom::geography))
                        FROM bornes_recharge b)
                   ) AS dist_borne_min_m
            FROM stations_metro m
            WHERE NOT EXISTS (
                SELECT 1 FROM bornes_recharge b
                WHERE ST_DWithin(m.geom::geography, b.geom::geography, %s)
            )
            ORDER BY dist_borne_min_m DESC
        """, [rayon])
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    return Response({"stations": rows, "count": len(rows), "rayon_m": rayon})


@api_view(["GET"])
def query_arrond_peu_equipes(request):
    """Arrondissements avec moins de N bornes (filtre sur nb_bornes)."""
    seuil = int(request.GET.get("seuil", 10))

    with connection.cursor() as cur:
        cur.execute("""
            SELECT nom, nb_bornes, ROUND(pct_couverture::numeric, 1) AS pct_couverture
            FROM arrondissements
            WHERE nb_bornes <= %s
            ORDER BY nb_bornes ASC, pct_couverture ASC
        """, [seuil])
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    return Response({"arrondissements": rows, "count": len(rows), "seuil": seuil})


@api_view(["GET"])
def gaps_geojson(request):
    """Zones géographiques sans couverture (output de gap_analysis.py)."""
    global _gaps_cache
    if _gaps_cache is None:
        path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "vectors",
                         "zones_sous_desservies.geojson")
        )
        if not os.path.exists(path):
            return Response({"type": "FeatureCollection", "features": []})
        with open(path, encoding="utf-8") as f:
            _gaps_cache = json.load(f)
    return Response(_gaps_cache)


@api_view(["GET"])
def equity_analysis(request):
    """Corrélation couverture ↔ profil socio-démographique (StatCan Recensement 2021)."""
    arronds = list(Arrondissement.objects.all().values("nom", "nb_bornes", "pct_couverture"))
    result = []
    for a in arronds:
        demo = _DEMO_DATA.get(a["nom"])
        if demo:
            result.append({
                "nom":             a["nom"],
                "nb_bornes":       a["nb_bornes"],
                "pct_couverture":  round(float(a["pct_couverture"] or 0), 1),
                "revenu_median":   demo["revenu_median"],
                "pop_2021":        demo["pop_2021"],
                "densite_pop":     demo["densite_pop"],
                "tx_voiture":      demo["tx_voiture"],
                "tx_faible_revenu": demo["tx_faible_revenu"],
            })
    result.sort(key=lambda x: x["revenu_median"])
    return Response({
        "arrondissements": result,
        "source": "StatCan, Recensement 2021 — données socio-démographiques par arrondissement",
    })


# ── NOUVELLES ANALYSES : PARCS, ÉPICERIES, PRIORITÉ ────────────────────────

@api_view(["GET"])
def query_parcs_sans_couverture(request):
    """
    Parcs sans couverture adéquate en bornes de recharge.
    Question gestionnaire : 'Tous les parcs de Montréal ont-ils ≥ N bornes à 500 m ?'
    Paramètre : n_bornes_min (défaut=20), rayon_m (défaut=500)
    """
    n_min  = int(request.GET.get("n_bornes_min", 20))
    rayon  = min(int(request.GET.get("rayon_m", 500)), 2000)

    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                p.id, p.nom, p.superficie_ha,
                ST_X(p.geom) AS lng, ST_Y(p.geom) AS lat,
                COUNT(b.id) AS nb_bornes_proches,
                ROUND(MIN(ST_Distance(p.geom::geography, b.geom::geography))) AS dist_borne_min_m
            FROM parcs p
            LEFT JOIN bornes_recharge b
                ON ST_DWithin(p.geom::geography, b.geom::geography, %s)
            GROUP BY p.id, p.nom, p.superficie_ha, p.geom
            HAVING COUNT(b.id) < %s
            ORDER BY nb_bornes_proches ASC, p.superficie_ha DESC
        """, [rayon, n_min])
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    # Total des parcs pour référence
    total_parcs = Parc.objects.count()
    return Response({
        "parcs_insuffisants": rows,
        "count":              len(rows),
        "total_parcs":        total_parcs,
        "pct_parcs_ok":       round(100 * (total_parcs - len(rows)) / max(total_parcs, 1), 1),
        "rayon_m":            rayon,
        "n_bornes_min":       n_min,
        "interpretation":     (
            f"{len(rows)} parcs sur {total_parcs} ont moins de {n_min} bornes "
            f"dans un rayon de {rayon} m. "
            f"Seulement {100 - round(100*len(rows)/max(total_parcs,1), 1)}% des parcs "
            f"atteignent le seuil cible."
        ),
    })


@api_view(["GET"])
def query_epiceries_sans_borne(request):
    """
    Épiceries sans borne de recharge à proximité.
    Question gestionnaire : 'Toutes les épiceries ont-elles des bornes à proximité ?'
    Paramètre : rayon_m (défaut=300)
    """
    rayon = min(int(request.GET.get("rayon_m", 300)), 1000)

    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                e.id, e.nom, e.type, e.adresse,
                ST_X(e.geom) AS lng, ST_Y(e.geom) AS lat,
                ROUND(MIN(ST_Distance(e.geom::geography, b.geom::geography))) AS dist_borne_min_m
            FROM epiceries e
            CROSS JOIN LATERAL (
                SELECT b.geom
                FROM bornes_recharge b
                ORDER BY e.geom::geography <-> b.geom::geography
                LIMIT 1
            ) b
            WHERE NOT EXISTS (
                SELECT 1 FROM bornes_recharge b2
                WHERE ST_DWithin(e.geom::geography, b2.geom::geography, %s)
            )
            GROUP BY e.id, e.nom, e.type, e.adresse, e.geom
            ORDER BY dist_borne_min_m DESC
        """, [rayon])
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    total_epiceries = Epicerie.objects.count()
    return Response({
        "epiceries_sans_borne": rows,
        "count":                len(rows),
        "total_epiceries":      total_epiceries,
        "pct_epiceries_ok":     round(100 * (total_epiceries - len(rows)) / max(total_epiceries, 1), 1),
        "rayon_m":              rayon,
        "interpretation":       (
            f"{len(rows)} épiceries sur {total_epiceries} n'ont aucune borne "
            f"dans un rayon de {rayon} m."
        ),
    })


@api_view(["GET"])
def priorite_installation(request):
    """
    Score de priorité pour l'installation de nouvelles bornes par arrondissement.
    Méthode : score composite multi-critères pondéré.

    Critères et pondérations :
      - Gap de couverture (1 - pct_couverture/100) : 35 %
      - Densité de population normalisée             : 25 %
      - Taux de motorisation (proxy demande EV)      : 15 %
      - Équité (favoriser faibles revenus)           : 15 %
      - Taux de faible revenu                        : 10 %

    Score final de 0 à 100 — plus le score est élevé, plus l'arrondissement
    est prioritaire pour de nouvelles installations.
    """
    arronds = list(Arrondissement.objects.all().values("nom", "nb_bornes", "pct_couverture"))

    # Enrichir avec données démographiques
    enriched = []
    for a in arronds:
        demo = _DEMO_DATA.get(a["nom"])
        if demo:
            enriched.append({**a, **demo})

    if not enriched:
        return Response({"arrondissements": [], "message": "Données démographiques non disponibles"})

    # Normaliser chaque critère entre 0 et 1
    max_densite = max(x["densite_pop"] for x in enriched)
    max_revenu  = max(x["revenu_median"] for x in enriched)
    max_voiture = max(x["tx_voiture"] for x in enriched)
    max_faible  = max(x["tx_faible_revenu"] for x in enriched)

    results = []
    for a in enriched:
        pct = float(a["pct_couverture"] or 0)
        gap_score     = (1 - pct / 100)                              # 35% — manque de couverture
        densite_score = a["densite_pop"] / max_densite               # 25% — plus dense = plus prioritaire
        voiture_score = a["tx_voiture"] / max_voiture                # 15% — plus de voitures = plus de demande EV potentielle
        equite_score  = 1 - (a["revenu_median"] / max_revenu)        # 15% — favoriser les zones moins aisées
        faiblerev_score = a["tx_faible_revenu"] / max_faible         # 10% — favoriser zones défavorisées

        score = (
            gap_score     * 0.35 +
            densite_score * 0.25 +
            voiture_score * 0.15 +
            equite_score  * 0.15 +
            faiblerev_score * 0.10
        ) * 100

        results.append({
            "nom":             a["nom"],
            "score_priorite":  round(score, 1),
            "pct_couverture":  round(pct, 1),
            "nb_bornes":       a["nb_bornes"],
            "pop_2021":        a["pop_2021"],
            "densite_pop":     a["densite_pop"],
            "revenu_median":   a["revenu_median"],
            "tx_voiture":      a["tx_voiture"],
            "tx_faible_revenu": a["tx_faible_revenu"],
            "detail_scores": {
                "gap_couverture":  round(gap_score * 0.35 * 100, 1),
                "densite":         round(densite_score * 0.25 * 100, 1),
                "motorisation":    round(voiture_score * 0.15 * 100, 1),
                "equite_revenu":   round(equite_score * 0.15 * 100, 1),
                "faible_revenu":   round(faiblerev_score * 0.10 * 100, 1),
            },
        })

    results.sort(key=lambda x: -x["score_priorite"])

    return Response({
        "arrondissements": results,
        "methodologie": {
            "description": "Score composite multi-critères 0-100 (plus élevé = plus prioritaire)",
            "criteres": {
                "gap_couverture": "35% — proportion du territoire sans borne à 500 m",
                "densite_population": "25% — densité d'habitants/km² (plus de résidents = plus de besoin)",
                "motorisation": "15% — taux de ménages avec véhicule (proxy demande EV)",
                "equite_revenu": "15% — favorise les zones à revenu médian plus faible",
                "faible_revenu": "10% — taux de ménages sous seuil de faible revenu",
            },
            "source_demo": "StatCan, Recensement 2021",
            "objectif": "Guider les gestionnaires de la Ville dans l'allocation des nouveaux équipements de recharge"
        }
    })


@api_view(["GET"])
def correlation_demo(request):
    """
    Corrélation multi-variable : couverture ↔ profil socio-démographique complet.
    Répond à : 'Les bornes dans les quartiers résidentiels sont-elles conditionnées
    au profil de la population ?'
    """
    arronds = list(Arrondissement.objects.all().values("nom", "nb_bornes", "pct_couverture"))
    result = []
    for a in arronds:
        demo = _DEMO_DATA.get(a["nom"])
        if not demo:
            continue
        pct = float(a["pct_couverture"] or 0)
        result.append({
            "nom":             a["nom"],
            "pct_couverture":  round(pct, 1),
            "nb_bornes":       a["nb_bornes"],
            "revenu_median":   demo["revenu_median"],
            "densite_pop":     demo["densite_pop"],
            "pop_2021":        demo["pop_2021"],
            "tx_voiture":      demo["tx_voiture"],
            "tx_faible_revenu": demo["tx_faible_revenu"],
        })

    # Pearson r pour chaque variable vs pct_couverture
    def pearson(xs, ys):
        n = len(xs)
        if n < 3:
            return 0
        mx = sum(xs) / n
        my = sum(ys) / n
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        dx  = sum((x - mx) ** 2 for x in xs) ** 0.5
        dy  = sum((y - my) ** 2 for y in ys) ** 0.5
        return round(num / (dx * dy + 1e-9), 3)

    covs = [a["pct_couverture"] for a in result]
    correlations = {
        "revenu_median":    pearson([a["revenu_median"]   for a in result], covs),
        "densite_pop":      pearson([a["densite_pop"]     for a in result], covs),
        "tx_voiture":       pearson([a["tx_voiture"]      for a in result], covs),
        "tx_faible_revenu": pearson([a["tx_faible_revenu"] for a in result], covs),
    }

    interpretations = {}
    for var, r in correlations.items():
        if abs(r) < 0.2:
            interpretations[var] = f"r={r} — corrélation faible : la couverture n'est pas liée à {var}"
        elif r > 0:
            interpretations[var] = f"r={r} — corrélation positive : zones avec {var} élevé sont mieux couvertes"
        else:
            interpretations[var] = f"r={r} — corrélation négative : zones avec {var} élevé sont moins couvertes"

    result.sort(key=lambda x: x["revenu_median"])
    return Response({
        "arrondissements":   result,
        "correlations_pearson": correlations,
        "interpretations":   interpretations,
        "question_recherche": "Les bornes dans les zones résidentielles sont-elles conditionnées au profil de la population ?",
        "source": "StatCan, Recensement 2021 — données socio-démographiques par arrondissement",
    })
