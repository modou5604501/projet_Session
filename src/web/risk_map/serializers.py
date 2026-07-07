from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework import serializers
from .models import BorneRecharge, ZoneCouverture, Arrondissement, StationMetro


class BorneRechargeSerializer(GeoFeatureModelSerializer):
    class Meta:
        model     = BorneRecharge
        geo_field = "geom"
        fields    = ["id", "nom", "type", "arrondissement", "nb_prises"]


class ZoneCouvertureSerializer(GeoFeatureModelSerializer):
    class Meta:
        model     = ZoneCouverture
        geo_field = "geom"
        fields    = ["id", "borne_id", "rayon_m"]


class ArrondissementSerializer(GeoFeatureModelSerializer):
    class Meta:
        model     = Arrondissement
        geo_field = "geom"
        fields    = ["id", "nom", "nb_bornes", "pct_couverture"]


class StationMetroSerializer(GeoFeatureModelSerializer):
    class Meta:
        model     = StationMetro
        geo_field = "geom"
        fields    = ["id", "nom", "ligne"]
