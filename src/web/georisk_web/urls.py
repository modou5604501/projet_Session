"""
URLs — GeoRisk Sentinel
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from risk_map import views

router = DefaultRouter()
router.register(r"electric", views.ElectricNetworkViewSet)
router.register(r"floods",   views.FloodZoneViewSet)
router.register(r"risks",    views.RiskAnalysisViewSet)
router.register(r"alerts",   views.AlerteViewSet)

urlpatterns = [
    path("admin/",              admin.site.urls),
    path("",                    views.map_view, name="map"),
    path("api/",                include(router.urls)),
    path("api/risk-summary/",   views.risk_summary,         name="risk-summary"),
    path("api/infra/<int:pk>/risk/", views.infrastructure_risk, name="infra-risk"),
]
