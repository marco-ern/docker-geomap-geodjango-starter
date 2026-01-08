import csv
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point

from core.models import Sismo


class Command(BaseCommand):
    help = "Carga sismos desde un archivo CSV del SSN"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            type=str,
            help="Ruta al archivo CSV de sismos (formato SSN)",
        )

    def handle(self, *args, **options):
        csv_path = options["csv_path"]

        count = 0

        try:
            csvfile = open(csv_path, newline="", encoding="latin-1")
        except Exception as e:
            raise CommandError(f"No se pudo abrir el archivo {csv_path}: {e}")

        with csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                try:
                    detalle = (row.get("Detalle") or "").strip()

                    fecha_utc = (row.get("Fecha UTC") or "").strip()
                    hora_utc = (row.get("Hora UTC") or "").strip()
                    if not fecha_utc or not hora_utc:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Fila sin Fecha UTC/Hora UTC, se omite: {row}"
                            )
                        )
                        continue

                    # <- AQUÍ está el cambio, usamos %d/%m/%Y
                    fecha_hora_utc = datetime.strptime(
                        f"{fecha_utc} {hora_utc}", "%d/%m/%Y %H:%M:%S"
                    )

                    latitud = float(row["Latitud"])
                    longitud = float(row["Longitud"])
                    profundidad_km = float(row["Profundidad (km)"])
                    magnitud = float(row["Magnitud"])
                    localizacion = (row.get("Localización") or "").strip()

                    punto = Point(longitud, latitud, srid=4326)

                    sismo, created = Sismo.objects.get_or_create(
                        fecha_hora_utc=fecha_hora_utc,
                        latitud=latitud,
                        longitud=longitud,
                        magnitud=magnitud,
                        defaults={
                            "detalle": detalle,
                            "profundidad_km": profundidad_km,
                            "localizacion": localizacion,
                            "ubicacion": punto,
                        },
                    )

                    if not created:
                        sismo.detalle = detalle
                        sismo.profundidad_km = profundidad_km
                        sismo.localizacion = localizacion
                        sismo.ubicacion = punto
                        sismo.save()

                    count += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error en fila {row}: {e}")
                    )

        self.stdout.write(
            self.style.SUCCESS(f"Sismos cargados/actualizados: {count}")
        )