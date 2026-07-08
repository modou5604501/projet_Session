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
    path("api/refresh/status/",          views.refresh_status,        name="refresh-status"),
    path("api/query/proches/",           views.query_bornes_proches,  name="query-proches"),
    path("api/query/rayon/",             views.query_bornes_rayon,    name="query-rayon"),
    path("api/query/metro-sans-borne/",  views.query_metro_sans_borne, name="query-metro"),
    path("api/query/arrond-peu-equipes/", views.query_arrond_peu_equipes, name="query-arrond"),
    path("api/gaps/",                    views.gaps_geojson,          name="gaps"),
    path("api/equity/",                  views.equity_analysis,       name="equity"),
    path("sw.js",                        views.serve_sw,              name="service-worker"),
]
