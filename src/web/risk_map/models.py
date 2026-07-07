from django.contrib.gis.db import models


class BorneRecharge(models.Model):
    nom            = models.CharField(max_length=200, null=True, blank=True)
    type           = models.CharField(max_length=50, null=True, blank=True)
    arrondissement = models.CharField(max_length=100, null=True, blank=True)
    nb_prises      = models.IntegerField(default=1)
    geom           = models.PointField(srid=4326)

    class Meta:
        db_table = "bornes_recharge"
        managed  = False

    def __str__(self):
        return f"{self.nom or 'Borne'} — {self.arrondissement or '?'}"


class ZoneCouverture(models.Model):
    borne   = models.ForeignKey(BorneRecharge, on_delete=models.CASCADE,
                                db_column="borne_id")
    rayon_m = models.IntegerField(default=500)
    geom    = models.PolygonField(srid=4326)

    class Meta:
        db_table = "zones_couverture"
        managed  = False

    def __str__(self):
        return f"Buffer {self.rayon_m}m — borne {self.borne_id}"


class Arrondissement(models.Model):
    nom            = models.CharField(max_length=100)
    nb_bornes      = models.IntegerField(default=0)
    pct_couverture = models.FloatField(default=0)
    geom           = models.MultiPolygonField(srid=4326)

    class Meta:
        db_table = "arrondissements"
        managed  = False

    def __str__(self):
        return self.nom


class StationMetro(models.Model):
    nom   = models.CharField(max_length=100)
    ligne = models.CharField(max_length=10, null=True, blank=True)
    geom  = models.PointField(srid=4326)

    class Meta:
        db_table = "stations_metro"
        managed  = False

    def __str__(self):
        return f"{self.nom} ({self.ligne})"
