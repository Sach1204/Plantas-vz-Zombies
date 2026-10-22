from app.domain.entities.usuario import Usuario
from app.domain.ports.salida import UsuariosPort


class SQLiteUsuarios(UsuariosPort):
    def __init__(self, base_datos):
        self.base_datos = base_datos

    def obtener_por_email(self, email):
        with self.base_datos.conectar() as conexion:
            fila = conexion.execute(
                "SELECT * FROM usuarios WHERE email = ?",
                (email.strip().lower(),),
            ).fetchone()
        if fila is None:
            return None
        return Usuario(
            id=fila["id"],
            email=fila["email"],
            hash_contrasena=fila["hash_contrasena"],
        )

    def guardar(self, usuario):
        with self.base_datos.conectar() as conexion:
            conexion.execute(
                """
                INSERT INTO usuarios (id, email, hash_contrasena)
                VALUES (?, ?, ?)
                """,
                (usuario.id, usuario.email, usuario.hash_contrasena),
            )
