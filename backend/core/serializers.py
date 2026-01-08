from rest_framework import serializers
from .models import Sismo

class SismoSerializer(serializers.ModelSerializer):
    coords = serializers.SerializerMethodField()

    class Meta:
        model = Sismo
        fields = (
            "id",
            "fecha_hora_utc",
            "latitud",
            "longitud",
            "profundidad_km",
            "magnitud",
            "localizacion",
            "coords",  # [lon, lat] para el mapa
        )

    def get_coords(self, obj):
        if obj.ubicacion:
            return [obj.ubicacion.x, obj.ubicacion.y]
        return [obj.longitud, obj.latitud]