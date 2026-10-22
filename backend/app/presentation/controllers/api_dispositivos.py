from datetime import datetime

from flask import Blueprint, current_app, g, jsonify, request

from app.domain.entities.especie import Especie
from app.domain.entities.lectura import Lectura, OrigenLectura
from app.domain.exceptions import DatoInvalido, DispositivoNoAutorizado
from app.presentation.security import requiere_dispositivo

api_dispositivos_bp = Blueprint(
    "api_dispositivos",
    __name__,
    url_prefix="/api/dispositivos",
)


@api_dispositivos_bp.post("/<dispositivo_id>/lecturas")
@requiere_dispositivo
def reportar_lectura(dispositivo_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise DatoInvalido("DATOS_DE_ENTRADA_INVALIDOS")
    if data.get("dispositivo_id") != dispositivo_id:
        raise DispositivoNoAutorizado("DISPOSITIVO_NO_AUTORIZADO")

    marca_temporal = data.get("marca_temporal")
    if not isinstance(marca_temporal, str):
        raise DatoInvalido("MARCA_TEMPORAL_INVALIDA")
    try:
        marca_temporal = datetime.fromisoformat(
            marca_temporal.replace("Z", "+00:00")
        )
    except ValueError:
        raise DatoInvalido("MARCA_TEMPORAL_INVALIDA") from None

    lectura = Lectura(
        especie=Especie(data.get("especie")),
        humedad=data.get("humedad"),
        luz=data.get("luz"),
        temperatura=data.get("temperatura"),
        marca_temporal=marca_temporal,
        dispositivo_id=dispositivo_id,
        planta_id=g.planta_id,
        origen=OrigenLectura.SENSOR,
    )
    diagnostico = current_app.extensions["matera"]["registrar_lectura"].ejecutar(
        lectura,
        dispositivo_id=g.dispositivo_id,
    )
    return jsonify(
        {
            "registrada": True,
            "estado": diagnostico.estado.value,
            "marca_temporal": marca_temporal.isoformat(),
        }
    ), 201
