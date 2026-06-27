"""
Sérialiseurs DRF pour l'API GeoJSON — GeoRisk Sentinel
"""

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import ElectricNetwork, FloodZone, RiskAnalysis, Alerte


class ElectricNetworkSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = ElectricNetwork
        geo_field = "geom"
        fields = ["id", "osm_id", "type", "voltage", "criticality"]


class FloodZoneSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = FloodZone
        geo_field = "geom"
        fields = ["id", "source", "date_detection", "recurrence", "surface_ha"]


class RiskAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskAnalysis
        fields = ["id", "infra_id", "niveau_risque", "distance_m", "date_analyse"]


class AlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerte
        fields = ["id", "niveau", "message", "infra_id", "date_alerte", "acquittee"]
