from django.contrib import admin
from .models import ElectricNetwork, FloodZone, RiskAnalysis, Alerte


@admin.register(ElectricNetwork)
class ElectricNetworkAdmin(admin.ModelAdmin):
    list_display = ["id", "osm_id", "type", "voltage", "criticality"]
    list_filter  = ["type", "criticality"]
    search_fields = ["osm_id", "type"]


@admin.register(FloodZone)
class FloodZoneAdmin(admin.ModelAdmin):
    list_display = ["id", "source", "date_detection", "surface_ha"]
    list_filter  = ["source"]


@admin.register(RiskAnalysis)
class RiskAnalysisAdmin(admin.ModelAdmin):
    list_display = ["id", "infra_id", "niveau_risque", "distance_m", "date_analyse"]
    list_filter  = ["niveau_risque"]


@admin.register(Alerte)
class AlerteAdmin(admin.ModelAdmin):
    list_display = ["id", "niveau", "message", "date_alerte", "acquittee"]
    list_filter  = ["niveau", "acquittee"]
    actions      = ["marquer_acquittee"]

    def marquer_acquittee(self, request, queryset):
        queryset.update(acquittee=True)
    marquer_acquittee.short_description = "Marquer comme acquittée"
