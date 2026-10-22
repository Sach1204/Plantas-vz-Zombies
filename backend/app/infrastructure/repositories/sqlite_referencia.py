from app.domain.entities.rango_referencia import RangoReferencia
from app.domain.ports.salida import TablaReferenciaPort


class SQLiteTablaReferencia(TablaReferenciaPort):
    def __init__(self, base_datos):
        self.base_datos = base_datos

    def obtener_por_especie(self, especie):
        nombre = getattr(especie, "nombre", especie)
        with self.base_datos.conectar() as conexion:
            fila = conexion.execute(
                "SELECT * FROM referencias WHERE especie = ?",
                (nombre,),
            ).fetchone()
        return self._a_rango(fila) if fila else None

    def listar_especies(self):
        with self.base_datos.conectar() as conexion:
            filas = conexion.execute(
                "SELECT * FROM referencias ORDER BY especie"
            ).fetchall()
        return [self._a_rango(fila) for fila in filas]

    @staticmethod
    def _a_rango(fila):
        return RangoReferencia(
            fila["especie"],
            fila["humedad_min"],
            fila["humedad_max"],
            fila["luz_min"],
            fila["luz_max"],
            fila["temperatura_min"],
            fila["temperatura_max"],
        )


def cargar_referencias_iniciales(base_datos, lector_csv):
    with base_datos.conectar() as conexion:
        cantidad = conexion.execute(
            "SELECT COUNT(*) AS total FROM referencias"
        ).fetchone()["total"]
        if cantidad:
            return
        referencias = lector_csv.listar_especies()
        conexion.executemany(
            """
            INSERT INTO referencias (
                especie, humedad_min, humedad_max, luz_min, luz_max,
                temperatura_min, temperatura_max
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    rango.especie,
                    rango.humedad_min,
                    rango.humedad_max,
                    rango.luz_min,
                    rango.luz_max,
                    rango.temperatura_min,
                    rango.temperatura_max,
                )
                for rango in referencias
            ],
        )
