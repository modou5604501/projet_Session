"""
Vues API et cartographiques — GeoRisk Sentinel
"""

from django.shortcuts import render
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import GEOSGeometry
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import ElectricNetwork, FloodZone, RiskAnalysis, Alerte
from .serializers import (
    ElectricNetworkSerializer,
    FloodZoneSerializer,
    RiskAnalysisSerializer,
    AlerteSerializer,
)


# ── Vue carte principale ──────────────────────────────────────────────────────

def map_view(request):
    """Page principale avec la carte Leaflet."""
    return render(request, "risk_map/map.html")


# ── ViewSets DRF ──────────────────────────────────────────────────────────────

class ElectricNetworkViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ElectricNetwork.objects.all()
    serializer_class = ElectricNetworkSerializer


class FloodZoneViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FloodZone.objects.all()
    serializer_class = FloodZoneSerializer


class RiskAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RiskAnalysis.objects.all()
    serializer_class = RiskAnalysisSerializer


class AlerteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Alerte.objects.filter(acquittee=False)
    serializer_class = AlerteSerializer


# ── Analyse de risque à la demande ───────────────────────────────────────────

@api_view(["GET"])
def risk_summary(request):
    """
    Résumé des risques : nombre d'infrastructures par niveau de risque,
    en croisant le réseau électrique avec les zones inondées.
    """
    # Récupération des zones inondées
    flood_zones = FloodZone.objects.all()
    if not flood_zones.exists():
        return Response({"error": "Aucune zone inondée dans la base"}, status=404)

    # Union de toutes les zones inondées
    from django.contrib.gis.db.models import Union
    union_qs = FloodZone.objects.aggregate(union=Union("geom"))
    flood_union = union_qs["union"]

    if flood_union is None:
        return Response({"error": "Géométries inondées invalides"}, status=500)

    # Infrastructure touchée directement (intersecte la zone inondée)
    direct = ElectricNetwork.objects.filter(geom__intersects=flood_union).count()

    # Infrastructure dans les 500 m des zones inondées
    buffer_500 = flood_union.buffer(500)
    proche_500 = (
        ElectricNetwork.objects
        .filter(geom__intersects=buffer_500)
        .exclude(geom__intersects=flood_union)
        .count()
    )

    total = ElectricNetwork.objects.count()

    return Response({
        "total_infrastructures": total,
        "critique": direct,
        "alerte_500m": proche_500,
        "hors_risque": max(0, total - direct - proche_500),
        "source_zones": flood_zones.count(),
    })


@api_view(["GET"])
def infrastructure_risk(request, pk):
    """
    Niveau de risque pour une infrastructure spécifique :
    distance à la zone inondée la plus proche.
    """
    try:
        infra = ElectricNetwork.objects.get(pk=pk)
    except ElectricNetwork.DoesNotExist:
        return Response({"error": "Infrastructure introuvable"}, status=404)

    flood_zones = FloodZone.objects.all()
    if not flood_zones.exists():
        return Response({"error": "Aucune zone inondée"}, status=404)

    # Calcul de la distance à la zone inondée la plus proche
    nearest = (
        FloodZone.objects
        .annotate(dist=Distance("geom", infra.geom))
        .order_by("dist")
        .first()
    )

    dist_m = nearest.dist.m if nearest else None

    if dist_m is None:
        niveau = "unknown"
    elif dist_m == 0:
        niveau = "critical"
    elif dist_m < 100:
        niveau = "high"
    elif dist_m < 500:
        niveau = "medium"
    else:
        niveau = "low"

    return Response({
        "infra_id": pk,
        "type": infra.type,
        "criticality": infra.criticality,
        "distance_flood_m": round(dist_m, 1) if dist_m is not None else None,
        "niveau_risque": niveau,
    })
