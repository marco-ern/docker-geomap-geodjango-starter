#from django.contrib import admin

# Register your models here.

''' Se recomienda usar la fuente SSN para agregar sismos, ya que contiene más detalles y son datos verificados. URL http://www2.ssn.unam.mx:8080/sismos-fuertes/
    Recuerde usar los datos con cautela y siempre citar la fuente SSN al publicar cualquier análisis o visualización basada en estos datos.
    se recomienda siempre consultar http://www.ssn.unam.mx/aviso-legal/'''

from django.contrib.gis import admin
from .models import Sismo


@admin.register(Sismo)
class SismoAdmin(admin.GISModelAdmin):
    list_display = ("fecha_hora_utc", "magnitud", "localizacion")

    # No permitir agregar nuevos sismos desde admin
    def has_add_permission(self, request):
        return False

    # Permitir ver listado y detalle, pero NO guardar cambios
    def has_change_permission(self, request, obj=None):
        # Permitir ver (GET/HEAD/OPTIONS) pero bloquear POST
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return False

    # Aun si alguien fuerza un POST, no guardar cambios
    def save_model(self, request, obj, form, change):
        # No hacemos nada: los cambios no se persisten
        return

    # No permitir borrar desde admin
    def has_delete_permission(self, request, obj=None):
        return False

    def delete_model(self, request, obj):
        # Bloquear borrados explícitos
        return