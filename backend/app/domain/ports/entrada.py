from abc import ABC, abstractmethod

from app.domain.entities.usuario_id import UsuarioId


class RegistrarLecturaPort(ABC):
    @abstractmethod
    def ejecutar(
        self,
        lectura,
        usuario_id: UsuarioId | None = None,
        dispositivo_id=None,
    ):
        raise NotImplementedError


class ConsultarEstadoPort(ABC):
    @abstractmethod
    def ejecutar(self, planta_id, usuario_id: UsuarioId):
        raise NotImplementedError


class ConsultarHistorialPort(ABC):
    @abstractmethod
    def ejecutar(self, planta_id, usuario_id: UsuarioId):
        raise NotImplementedError


class ListarPlantasPort(ABC):
    @abstractmethod
    def ejecutar(self, usuario_id: UsuarioId):
        raise NotImplementedError


class ListarEspeciesPort(ABC):
    @abstractmethod
    def ejecutar(self):
        raise NotImplementedError
