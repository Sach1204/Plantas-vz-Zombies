from abc import ABC, abstractmethod

from app.domain.entities.usuario_id import UsuarioId


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
    def listar_por_usuario(self, usuario_id: UsuarioId):
        raise NotImplementedError

    @abstractmethod
    def obtener_por_dispositivo(self, dispositivo_id):
        raise NotImplementedError

    @abstractmethod
    def actualizar(self, planta):
        raise NotImplementedError

    @abstractmethod
    def eliminar(self, planta_id):
        raise NotImplementedError


class UsuariosPort(ABC):
    @abstractmethod
    def obtener_por_email(self, email):
        raise NotImplementedError

    @abstractmethod
    def obtener_por_id(self, usuario_id: UsuarioId):
        raise NotImplementedError

    @abstractmethod
    def guardar(self, usuario):
        raise NotImplementedError

    @abstractmethod
    def actualizar_contrasena(self, email, hash_contrasena):
        raise NotImplementedError


class ColaboradoresPort(ABC):
    @abstractmethod
    def agregar_colaborador(self, planta_id, usuario_id: UsuarioId, rol="CUIDADOR"):
        raise NotImplementedError

    @abstractmethod
    def listar_colaboradores(self, planta_id):
        raise NotImplementedError

    @abstractmethod
    def es_colaborador(self, planta_id, usuario_id: UsuarioId):
        raise NotImplementedError

    @abstractmethod
    def registrar_actividad(self, planta_id, usuario_id: UsuarioId, accion, marca_temporal):
        raise NotImplementedError

    @abstractmethod
    def listar_actividades(self, planta_id, limite=20):
        raise NotImplementedError


class EmisorTokenPort(ABC):
    @abstractmethod
    def emitir_usuario(self, usuario_id: UsuarioId):
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
