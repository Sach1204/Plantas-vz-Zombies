import csv

from app.domain.entities.rango_referencia import RangoReferencia


class CSVReferenciaPlantas:

    def __init__(self, ruta):
        self.ruta = ruta

    def obtener_por_especie(self, especie):

        with open(self.ruta, newline="", encoding="utf-8") as archivo:
            lector = csv.DictReader(archivo)

            for fila in lector:
                if fila["especie"].lower() == especie.lower():
                    return RangoReferencia(
                        fila["especie"],
                        float(fila["humedad_min"]),
                        float(fila["humedad_max"]),
                        float(fila["luz_min"]),
                        float(fila["luz_max"]),
                        float(fila["temp_min"]),
                        float(fila["temp_max"])
                    )

        return None

    def listar_especies(self):

        especies = []

        with open(self.ruta, newline="", encoding="utf-8") as archivo:
            lector = csv.DictReader(archivo)

            for fila in lector:
                especies.append(
                    RangoReferencia(
                        fila["especie"],
                        float(fila["humedad_min"]),
                        float(fila["humedad_max"]),
                        float(fila["luz_min"]),
                        float(fila["luz_max"]),
                        float(fila["temp_min"]),
                        float(fila["temp_max"])
                    )
                )

        return especies
