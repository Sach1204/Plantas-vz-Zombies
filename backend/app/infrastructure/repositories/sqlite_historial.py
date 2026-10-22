from datetime import datetime

from app.domain.entities.especie import Especie
from app.domain.entities.lectura import Lectura, OrigenLectura
from app.domain.ports.salida import HistorialLecturasPort


class SQLiteHistorialLecturas(HistorialLecturasPort):
    def __init__(self, base_datos):
        self.base_datos = base_datos

    def guardar(self, lectura):
        with self.base_datos.conectar() as conexion:
            conexion.execute(
                """
                INSERT INTO lecturas (
                    planta_id, dispositivo_id, marca_temporal, especie,
                    humedad, luz, temperatura, origen
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lectura.planta_id,
                    lectura.dispositivo_id,
                    lectura.marca_temporal.isoformat(),
                    lectura.especie.nombre,
                    lectura.humedad,
                    lectura.luz,
                    lectura.temperatura,
                    lectura.origen.value,
                ),
            )

    def listar_por_planta(self, planta_id):
        with self.base_datos.conectar() as conexion:
            filas = conexion.execute(
                """
                SELECT * FROM lecturas
                WHERE planta_id = ?
                ORDER BY marca_temporal DESC, id DESC
                """,
                (planta_id,),
            ).fetchall()
        return [self._a_lectura(fila) for fila in filas]

    def ultima_por_planta(self, planta_id):
        with self.base_datos.conectar() as conexion:
            fila = conexion.execute(
                """
                SELECT * FROM lecturas
                WHERE planta_id = ?
                ORDER BY marca_temporal DESC, id DESC
                LIMIT 1
                """,
                (planta_id,),
            ).fetchone()
        return self._a_lectura(fila) if fila else None

    @staticmethod
    def _a_lectura(fila):
        return Lectura(
            especie=Especie(fila["especie"]),
            humedad=fila["humedad"],
            luz=fila["luz"],
            temperatura=fila["temperatura"],
            marca_temporal=datetime.fromisoformat(fila["marca_temporal"]),
            dispositivo_id=fila["dispositivo_id"],
            planta_id=fila["planta_id"],
            origen=OrigenLectura(fila["origen"]),
        )
