from app.domain.services.evaluador_planta import EvaluadorPlanta
from app.domain.entities.estado_parametro import EstadoParametro


def test_humedad_baja():
    evaluador = EvaluadorPlanta()

    resultado = evaluador.evaluar_parametro(
        "humedad",
        10,
        20,
        45,
        "%"
    )

    assert resultado.estado == EstadoParametro.BAJO


def test_humedad_optima():
    evaluador = EvaluadorPlanta()

    resultado = evaluador.evaluar_parametro(
        "humedad",
        30,
        20,
        45,
        "%"
    )

    assert resultado.estado == EstadoParametro.OPTIMO


def test_humedad_alta():
    evaluador = EvaluadorPlanta()

    resultado = evaluador.evaluar_parametro(
        "humedad",
        60,
        20,
        45,
        "%"
    )

    assert resultado.estado == EstadoParametro.ALTO
