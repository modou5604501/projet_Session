from django.contrib import admin
from .models import BorneRecharge, ZoneCouverture, Arrondissement, StationMetro


@admin.register(BorneRecharge)
class BorneRechargeAdmin(admin.ModelAdmin):
    list_display  = ["id", "nom", "type", "arrondissement", "nb_prises"]
    list_filter   = ["arrondissement", "type"]
    search_fields = ["nom", "arrondissement"]


@admin.register(Arrondissement)
class ArrondissementAdmin(admin.ModelAdmin):
    list_display = ["id", "nom", "nb_bornes", "pct_couverture"]
    ordering     = ["pct_couverture"]


@admin.register(StationMetro)
class StationMetroAdmin(admin.ModelAdmin):
    list_display  = ["id", "nom", "ligne"]
    list_filter   = ["ligne"]
    search_fields = ["nom"]


@admin.register(ZoneCouverture)
class ZoneCouvertureAdmin(admin.ModelAdmin):
    list_display = ["id", "borne_id", "rayon_m"]
