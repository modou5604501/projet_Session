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

from .models import BorneRecharge, ZoneCouverture, Arrondissement, StationMetro
from .serializers import (
    BorneRechargeSerializer,
    ZoneCouvertureSerializer,
    ArrondissementSerializer,
    StationMetroSerializer,
)

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
