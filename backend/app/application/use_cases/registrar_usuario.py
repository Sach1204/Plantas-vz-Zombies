from uuid import uuid4

from app.domain.entities.usuario import Usuario
from app.domain.exceptions import DatoInvalido


class RegistrarUsuario:
    def __init__(self, usuarios, hash_contrasenas, emisor_token):
        self.usuarios = usuarios
        self.hash_contrasenas = hash_contrasenas
        self.emisor_token = emisor_token

    def ejecutar(self, email, contrasena):
        if not isinstance(email, str) or not isinstance(contrasena, str):
            raise DatoInvalido("DATOS_DE_ENTRADA_INVALIDOS")
        email = email.strip().lower()
        if not email or len(contrasena) < 8:
            raise DatoInvalido("DATOS_DE_ENTRADA_INVALIDOS")
        if self.usuarios.obtener_por_email(email) is not None:
            raise DatoInvalido("USUARIO_YA_REGISTRADO")

        usuario = Usuario(
            id=str(uuid4()),
            email=email,
            hash_contrasena=self.hash_contrasenas.generar(contrasena),
        )
        self.usuarios.guardar(usuario)
        return usuario, self.emisor_token.emitir_usuario(usuario.id)
