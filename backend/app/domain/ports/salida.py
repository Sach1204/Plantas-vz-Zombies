from abc import ABC, abstractmethod


class TablaReferenciaPort(ABC):
    @abstractmethod
    def obtener_por_especie(self, especie):
        raise NotImplementedError

    @abstractmethod
    def listar_especies(self):
        raise NotImplementedError


class HistorialLecturasPort(ABC):
    @abstractmethod
    def guardar(self, lectura):
        raise NotImplementedError

    @abstractmethod
    def listar_por_planta(self, planta_id):
        raise NotImplementedError

    @abstractmethod
    def ultima_por_planta(self, planta_id):
        raise NotImplementedError


class PlantasPort(ABC):
    @abstractmethod
    def guardar(self, planta):
        raise NotImplementedError

    @abstractmethod
    def obtener(self, planta_id):
        raise NotImplementedError

    @abstractmethod
    def listar_por_usuario(self, usuario_id):
        raise NotImplementedError

    @abstractmethod
    def obtener_por_dispositivo(self, dispositivo_id):
        raise NotImplementedError


class UsuariosPort(ABC):
    @abstractmethod
    def obtener_por_email(self, email):
        raise NotImplementedError

    @abstractmethod
    def guardar(self, usuario):
        raise NotImplementedError


class EmisorTokenPort(ABC):
    @abstractmethod
    def emitir_usuario(self, usuario_id):
        raise NotImplementedError

    @abstractmethod
    def emitir_dispositivo(self, dispositivo_id, planta_id):
        raise NotImplementedError


class HashContrasenasPort(ABC):
    @abstractmethod
    def generar(self, contrasena):
        raise NotImplementedError

    @abstractmethod
    def verificar(self, hash_contrasena, contrasena):
        raise NotImplementedError
