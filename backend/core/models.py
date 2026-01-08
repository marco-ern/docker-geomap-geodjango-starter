#from django.db import models

# Create your models here.

from django.contrib.gis.db import models

class Sismo(models.Model):
    detalle = models.CharField(max_length=255, blank=True)  # <- NUEVO CAMPO
    fecha_hora_utc = models.DateTimeField()
    latitud = models.FloatField()
    longitud = models.FloatField()
    profundidad_km = models.FloatField()
    magnitud = models.FloatField()
    localizacion = models.CharField(max_length=255)
    ubicacion = models.PointField(srid=4326)

    class Meta:
        ordering = ["-fecha_hora_utc"]

    def __str__(self):
        return f"{self.fecha_hora_utc} M{self.magnitud} - {self.localizacion}"