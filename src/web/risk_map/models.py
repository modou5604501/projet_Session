"""
Modèles GeoDjango — GeoRisk Sentinel
Correspond aux tables créées dans sql/01_create_tables.sql
"""

from django.contrib.gis.db import models


class ElectricNetwork(models.Model):
    osm_id      = models.BigIntegerField(null=True, blank=True)
    type        = models.CharField(max_length=50, null=True, blank=True)
    voltage     = models.IntegerField(null=True, blank=True)
    criticality = models.CharField(max_length=20, default="medium")
    geom        = models.GeometryField(srid=32198)

    class Meta:
        db_table = "electric_network"
        managed  = False

    def __str__(self):
        return f"{self.type or 'infra'} [{self.osm_id}]"


class FloodZone(models.Model):
    source          = models.CharField(max_length=50, null=True)
    date_detection  = models.DateField(null=True, blank=True)
    recurrence      = models.IntegerField(null=True, blank=True)
    surface_ha      = models.FloatField(null=True, blank=True)
    geom            = models.MultiPolygonField(srid=32198, null=True)

    class Meta:
        db_table = "flood_zones"
        managed  = False

    def __str__(self):
        return f"Zone inondee {self.id} ({self.surface_ha:.1f} ha)" if self.surface_ha else f"Zone {self.id}"


class RiskAnalysis(models.Model):
    RISK_CHOICES = [
        ("low",      "Faible"),
        ("medium",   "Moyen"),
        ("high",     "Eleve"),
        ("critical", "Critique"),
    ]
    infra         = models.ForeignKey(ElectricNetwork, on_delete=models.CASCADE,
                                      db_column="infra_id", null=True)
    niveau_risque = models.CharField(max_length=20, choices=RISK_CHOICES)
    distance_m    = models.FloatField(null=True)
    date_analyse  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "risk_analysis"
        managed  = False

    def __str__(self):
        return f"Risque {self.niveau_risque} infra {self.infra_id}"


class Alerte(models.Model):
    LEVEL_CHOICES = [
        ("info",     "Information"),
        ("warning",  "Avertissement"),
        ("critical", "Critique"),
    ]
    niveau      = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    message     = models.TextField()
    infra       = models.ForeignKey(ElectricNetwork, on_delete=models.SET_NULL,
                                    db_column="infra_id", null=True, blank=True)
    date_alerte = models.DateTimeField(auto_now_add=True)
    acquittee   = models.BooleanField(default=False)

    class Meta:
        db_table = "alertes"
        managed  = False
        ordering = ["-date_alerte"]

    def __str__(self):
        return f"[{self.niveau}] {self.message[:50]}"
