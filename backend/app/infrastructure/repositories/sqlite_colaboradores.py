from app.domain.entities.usuario_id import UsuarioId
from app.domain.ports.salida import ColaboradoresPort


class SQLiteColaboradores(ColaboradoresPort):
    def __init__(self, base_datos):
        self.base_datos = base_datos

    def agregar_colaborador(self, planta_id, usuario_id: UsuarioId, rol="CUIDADOR"):
        from datetime import datetime, timezone

        ahora = datetime.now(timezone.utc).isoformat()
        with self.base_datos.conectar() as conexion:
            conexion.execute(
                """
                INSERT OR REPLACE INTO colaboradores (planta_id, usuario_id, rol, creado_en)
                VALUES (?, ?, ?, ?)
                """,
                (planta_id, str(usuario_id), rol, ahora),
            )

    def listar_colaboradores(self, planta_id):
        with self.base_datos.conectar() as conexion:
            filas = conexion.execute(
                """
                SELECT usuario_id, rol, creado_en
                FROM colaboradores
                WHERE planta_id = ?
                ORDER BY creado_en ASC
                """,
                (planta_id,),
            ).fetchall()
        return [
            {
                "usuario_id": UsuarioId(fila["usuario_id"]),
                "rol": fila["rol"],
                "creado_en": fila["creado_en"],
            }
            for fila in filas
        ]

    def es_colaborador(self, planta_id, usuario_id: UsuarioId):
        with self.base_datos.conectar() as conexion:
            fila = conexion.execute(
                """
                SELECT 1 FROM colaboradores
                WHERE planta_id = ? AND usuario_id = ?
                """,
                (planta_id, str(usuario_id)),
            ).fetchone()
        return fila is not None

    def registrar_actividad(self, planta_id, usuario_id: UsuarioId, accion, marca_temporal):
        with self.base_datos.conectar() as conexion:
            conexion.execute(
                """
                INSERT INTO actividades (planta_id, usuario_id, accion, marca_temporal)
                VALUES (?, ?, ?, ?)
                """,
                (planta_id, str(usuario_id), accion, marca_temporal),
            )

    def listar_actividades(self, planta_id, limite=20):
        with self.base_datos.conectar() as conexion:
            filas = conexion.execute(
                """
                SELECT id, planta_id, usuario_id, accion, marca_temporal
                FROM actividades
                WHERE planta_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (planta_id, limite),
            ).fetchall()
        return [
            {
                "id": fila["id"],
                "planta_id": fila["planta_id"],
                "usuario_id": UsuarioId(fila["usuario_id"]),
                "accion": fila["accion"],
                "marca_temporal": fila["marca_temporal"],
            }
            for fila in filas
        ]

