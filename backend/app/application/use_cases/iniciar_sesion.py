from app.domain.exceptions import DatoInvalido


class IniciarSesion:
    def __init__(self, usuarios, hash_contrasenas, emisor_token):
        self.usuarios = usuarios
        self.hash_contrasenas = hash_contrasenas
        self.emisor_token = emisor_token

    def ejecutar(self, email, contrasena):
        if not isinstance(email, str) or not isinstance(contrasena, str):
            raise DatoInvalido("CREDENCIALES_INVALIDAS")
        usuario = self.usuarios.obtener_por_email(email.strip().lower())
        if usuario is None or not self.hash_contrasenas.verificar(
            usuario.hash_contrasena,
            contrasena,
        ):
            raise DatoInvalido("CREDENCIALES_INVALIDAS")
        return usuario, self.emisor_token.emitir_usuario(usuario.id)
