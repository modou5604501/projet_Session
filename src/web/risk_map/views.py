import sys
import os
import threading
from django.shortcuts import render
import pandas as pd
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


@api_view(["GET"])
def priority_zones(request):
    """Classe les arrondissements selon un score de priorite de developpement."""
    csv_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "vectors", "priorites_arrondissements.csv")
    )

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        records = df.to_dict(orient="records")
        for rec in records:
            rec["rang"] = int(rec.get("rang", 0))
            rec["score_priorite"] = round(float(rec.get("score_priorite", 0.0)), 4)

        return Response({
            "count": len(records),
            "source": "precomputed_csv_with_road_network",
            "weights": {
                "deficit_couverture": 0.25,
                "distance_reseau": 0.25,
                "demographie": 0.20,
                "potentiel_demande": 0.15,
                "pression_equipement": 0.10,
                "criticite": 0.05,
            },
            "results": records,
        })

    return Response(
        {
            "count": 0,
            "source": "missing_precomputed_priorities",
            "message": (
                "Le fichier data/vectors/priorites_arrondissements.csv est absent. "
                "Executez d'abord: python src/preprocessing/prioritization_analysis.py"
            ),
            "results": [],
        },
        status=503,
    )
