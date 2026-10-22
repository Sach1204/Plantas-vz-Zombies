from app.domain.entities.especie import Especie
from app.domain.entities.planta import Planta
from app.domain.ports.salida import PlantasPort


class SQLitePlantas(PlantasPort):
    def __init__(self, base_datos):
        self.base_datos = base_datos

    def guardar(self, planta):
        with self.base_datos.conectar() as conexion:
            conexion.execute(
                """
                INSERT INTO plantas (id, nombre, especie, propietario_id, dispositivo_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    planta.id,
                    planta.nombre.strip(),
                    planta.especie.nombre,
                    planta.propietario_id,
                    planta.dispositivo_id,
                ),
            )

    def obtener(self, planta_id):
        with self.base_datos.conectar() as conexion:
            fila = conexion.execute(
                "SELECT * FROM plantas WHERE id = ?",
                (planta_id,),
            ).fetchone()
        return self._a_planta(fila) if fila else None

    def listar_por_usuario(self, usuario_id):
        with self.base_datos.conectar() as conexion:
            filas = conexion.execute(
                "SELECT * FROM plantas WHERE propietario_id = ? ORDER BY nombre",
                (usuario_id,),
            ).fetchall()
        return [self._a_planta(fila) for fila in filas]

    def obtener_por_dispositivo(self, dispositivo_id):
        with self.base_datos.conectar() as conexion:
            fila = conexion.execute(
                "SELECT * FROM plantas WHERE dispositivo_id = ?",
                (dispositivo_id,),
            ).fetchone()
        return self._a_planta(fila) if fila else None

    @staticmethod
    def _a_planta(fila):
        return Planta(
            id=fila["id"],
            nombre=fila["nombre"],
            especie=Especie(fila["especie"]),
            propietario_id=fila["propietario_id"],
            dispositivo_id=fila["dispositivo_id"],
        )
