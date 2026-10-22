from abc import ABC, abstractmethod


class RegistrarLecturaPort(ABC):
    @abstractmethod
    def ejecutar(self, lectura, usuario_id=None, dispositivo_id=None):
        raise NotImplementedError


class ConsultarEstadoPort(ABC):
    @abstractmethod
    def ejecutar(self, planta_id, usuario_id):
        raise NotImplementedError


class ConsultarHistorialPort(ABC):
    @abstractmethod
    def ejecutar(self, planta_id, usuario_id):
        raise NotImplementedError


class ListarPlantasPort(ABC):
    @abstractmethod
    def ejecutar(self, usuario_id):
        raise NotImplementedError


class ListarEspeciesPort(ABC):
    @abstractmethod
    def ejecutar(self):
        raise NotImplementedError
