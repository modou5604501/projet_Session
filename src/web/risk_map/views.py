from django.shortcuts import render
from django.contrib.gis.db.models import Union
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
    arrondissements = Arrondissement.objects.all().values(
        "nom", "nb_bornes", "pct_couverture"
    ).order_by("pct_couverture")

    total_bornes = BorneRecharge.objects.count()

    sous_desservis = [
        a for a in arrondissements if a["pct_couverture"] < 30
    ]

    return Response({
        "total_bornes":        total_bornes,
        "total_arrondissements": Arrondissement.objects.count(),
        "sous_desservis":      len(sous_desservis),
        "arrondissements":     list(arrondissements),
    })
