from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from risk_map import views

router = DefaultRouter()
router.register(r"bornes",        views.BorneRechargeViewSet)
router.register(r"couverture",    views.ZoneCouvertureViewSet)
router.register(r"arrondissements", views.ArrondissementViewSet)
router.register(r"metro",         views.StationMetroViewSet)

urlpatterns = [
    path("admin/",                admin.site.urls),
    path("",                      views.map_view,        name="map"),
    path("api/",                  include(router.urls)),
    path("api/coverage-summary/", views.coverage_summary, name="coverage-summary"),
    path("api/refresh/",          views.trigger_refresh,  name="trigger-refresh"),
    path("api/refresh/status/",   views.refresh_status,   name="refresh-status"),
    path("sw.js",                  views.serve_sw,         name="service-worker"),
]
