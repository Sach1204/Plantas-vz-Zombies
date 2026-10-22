from dataclasses import dataclass

from app.domain.exceptions import DatoInvalido
from app.domain.entities.usuario_id import UsuarioId


@dataclass(frozen=True)
class Usuario:
    id: UsuarioId
    email: str
    hash_contrasena: str

    def __post_init__(self):
        if not self.id or not self.hash_contrasena or "@" not in self.email:
            raise DatoInvalido("USUARIO_INVALIDO")
        object.__setattr__(self, "id", UsuarioId(self.id))
        object.__setattr__(self, "email", self.email.strip().lower())
