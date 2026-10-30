from app.domain.exceptions import DatoInvalido, RecursoNoEncontrado


class RecuperarContrasena:
    def __init__(self, usuarios, hash_contrasenas):
        self.usuarios = usuarios
        self.hash_contrasenas = hash_contrasenas

    def ejecutar(self, email, nueva_contrasena):
        if not isinstance(email, str) or not isinstance(nueva_contrasena, str):
            raise DatoInvalido("DATOS_INVALIDOS")
        if len(nueva_contrasena) < 8:
            raise DatoInvalido("CONTRASENA_DEMASIADO_CORTA")

        usuario = self.usuarios.obtener_por_email(email.strip().lower())
        if usuario is None:
            raise RecursoNoEncontrado("USUARIO_NO_ENCONTRADO")

        nuevo_hash = self.hash_contrasenas.generar(nueva_contrasena)
        self.usuarios.actualizar_contrasena(email.strip().lower(), nuevo_hash)
        return True

