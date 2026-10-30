from datetime import datetime, timezone
from app.domain.entities.usuario_id import UsuarioId
from app.domain.exceptions import AccesoDenegado, DatoInvalido, RecursoNoEncontrado


class InvitarColaborador:
    def __init__(self, plantas, usuarios, colaboradores):
        self.plantas = plantas
        self.usuarios = usuarios
        self.colaboradores = colaboradores

    def ejecutar(self, planta_id, usuario_id: UsuarioId, email_colaborador):
        planta = self.plantas.obtener(planta_id)
        if planta is None:
            raise RecursoNoEncontrado("PLANTA_NO_ENCONTRADA")
        planta.asegurar_propietario(usuario_id)

        colaborador = self.usuarios.obtener_por_email(email_colaborador.strip().lower())
        if colaborador is None:
            raise RecursoNoEncontrado("USUARIO_NO_ENCONTRADO")
        if colaborador.id == usuario_id:
            raise DatoInvalido("NO_PUEDES_INVITARTE_A_TI_MISMO")

        self.colaboradores.agregar_colaborador(planta_id, colaborador.id, rol="CUIDADOR")
        return {
            "planta_id": planta_id,
            "usuario_id": colaborador.id,
            "email": colaborador.email,
            "rol": "CUIDADOR",
        }


class ListarEquipoCuidado:
    def __init__(self, plantas, usuarios, colaboradores):
        self.plantas = plantas
        self.usuarios = usuarios
        self.colaboradores = colaboradores

    def ejecutar(self, planta_id, usuario_id: UsuarioId):
        planta = self.plantas.obtener(planta_id)
        if planta is None:
            raise RecursoNoEncontrado("PLANTA_NO_ENCONTRADA")
        es_dueno = planta.propietario_id == usuario_id
        es_colab = self.colaboradores.es_colaborador(planta_id, usuario_id)
        if not (es_dueno or es_colab):
            raise AccesoDenegado("ACCESO_DENEGADO")

        propietario = self.usuarios.obtener_por_id(planta.propietario_id)
        equipo = [
            {
                "usuario_id": str(planta.propietario_id),
                "email": propietario.email if propietario else "Propietario",
                "rol": "PROPIETARIO",
                "es_dueno": True,
            }
        ]
        for colab in self.colaboradores.listar_colaboradores(planta_id):
            usr = self.usuarios.obtener_por_id(colab["usuario_id"])
            equipo.append(
                {
                    "usuario_id": str(colab["usuario_id"]),
                    "email": usr.email if usr else str(colab["usuario_id"]),
                    "rol": colab.get("rol", "CUIDADOR"),
                    "es_dueno": False,
                }
            )
        return equipo


class RegistrarActividad:
    def __init__(self, plantas, colaboradores):
        self.plantas = plantas
        self.colaboradores = colaboradores

    def ejecutar(self, planta_id, usuario_id: UsuarioId, accion):
        planta = self.plantas.obtener(planta_id)
        if planta is None:
            raise RecursoNoEncontrado("PLANTA_NO_ENCONTRADA")
        es_dueno = planta.propietario_id == usuario_id
        es_colab = self.colaboradores.es_colaborador(planta_id, usuario_id)
        if not (es_dueno or es_colab):
            raise AccesoDenegado("ACCESO_DENEGADO")

        marca = datetime.now(timezone.utc).isoformat()
        self.colaboradores.registrar_actividad(planta_id, usuario_id, accion, marca)
        return {
            "planta_id": planta_id,
            "usuario_id": str(usuario_id),
            "accion": accion,
            "marca_temporal": marca,
        }


class ListarActividades:
    def __init__(self, plantas, usuarios, colaboradores):
        self.plantas = plantas
        self.usuarios = usuarios
        self.colaboradores = colaboradores

    def ejecutar(self, planta_id, usuario_id: UsuarioId):
        planta = self.plantas.obtener(planta_id)
        if planta is None:
            raise RecursoNoEncontrado("PLANTA_NO_ENCONTRADA")
        es_dueno = planta.propietario_id == usuario_id
        es_colab = self.colaboradores.es_colaborador(planta_id, usuario_id)
        if not (es_dueno or es_colab):
            raise AccesoDenegado("ACCESO_DENEGADO")

        filas = self.colaboradores.listar_actividades(planta_id)
        resultado = []
        for fila in filas:
            usr = self.usuarios.obtener_por_id(fila["usuario_id"])
            resultado.append(
                {
                    "id": fila["id"],
                    "accion": fila["accion"],
                    "marca_temporal": fila["marca_temporal"],
                    "usuario_email": usr.email if usr else "Usuario",
                }
            )
        return resultado

