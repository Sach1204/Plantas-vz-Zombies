from werkzeug.security import check_password_hash, generate_password_hash

from app.domain.ports.salida import HashContrasenasPort


class WerkzeugHashContrasenas(HashContrasenasPort):
    def generar(self, contrasena):
        return generate_password_hash(contrasena)

    def verificar(self, hash_contrasena, contrasena):
        return check_password_hash(hash_contrasena, contrasena)
