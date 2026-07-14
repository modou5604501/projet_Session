from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from risk_map import views

router = DefaultRouter()
router.register(r"bornes",          views.BorneRechargeViewSet)
router.register(r"couverture",      views.ZoneCouvertureViewSet)
router.register(r"arrondissements", views.ArrondissementViewSet)
router.register(r"metro",           views.StationMetroViewSet)
router.register(r"parcs",           views.ParcViewSet)
router.register(r"epiceries",       views.EpicerieViewSet)

urlpatterns = [
    path("admin/",                admin.site.urls),
    path("",                      views.map_view,        name="map"),
    path("api/",                  include(router.urls)),
    # Résumé et refresh
    path("api/coverage-summary/",       views.coverage_summary,             name="coverage-summary"),
    path("api/refresh/",                views.trigger_refresh,              name="trigger-refresh"),
    path("api/refresh/status/",         views.refresh_status,               name="refresh-status"),
    # Requêtes spatiales classiques
    path("api/query/proches/",           views.query_bornes_proches,         name="query-proches"),
    path("api/query/rayon/",             views.query_bornes_rayon,           name="query-rayon"),
    path("api/query/metro-sans-borne/",  views.query_metro_sans_borne,       name="query-metro"),
    path("api/query/arrond-peu-equipes/", views.query_arrond_peu_equipes,    name="query-arrond"),
    # Zones
    path("api/gaps/",                    views.gaps_geojson,                 name="gaps"),
    # Analyses socio-démographiques
    path("api/equity/",                  views.equity_analysis,              name="equity"),
    path("api/correlation/",             views.correlation_demo,             name="correlation"),
    # Nouvelles analyses gestionnaire
    path("api/query/parcs-sans-couverture/", views.query_parcs_sans_couverture, name="query-parcs"),
    path("api/query/epiceries-sans-borne/",  views.query_epiceries_sans_borne,  name="query-epiceries"),
    path("api/priorite/",                    views.priorite_installation,        name="priorite"),
    # Réseau routier
    path("api/reseau-routier/",              views.reseau_routier_geojson,        name="reseau-routier"),
    # PWA
    path("sw.js",                        views.serve_sw,                     name="service-worker"),
]
