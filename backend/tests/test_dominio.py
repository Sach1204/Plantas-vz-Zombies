import pytest

from app.application.use_cases.diagnosticar_planta import DiagnosticarPlanta
from app.domain.entities.medicion import Medicion
from app.domain.entities.rango_referencia import RangoReferencia
from app.domain.services.evaluador_planta import EvaluadorPlanta
from app.domain.services.recomendador import Recomendador


class FakeReferenciaPlantas:
    def __init__(self, especies):
        self._especies = {especie.especie.lower(): especie for especie in especies}

    def obtener_por_especie(self, especie):
        return self._especies.get(especie.lower())

    def listar_especies(self):
        return list(self._especies.values())


@pytest.fixture
def referencia_sansevieria():
    return FakeReferenciaPlantas([
        RangoReferencia(
            "sansevieria",
            30,
            60,
            300,
            800,
            18,
            28,
        )
    ])


@pytest.fixture
def evaluador():
    return EvaluadorPlanta()


def test_evaluador_parametro_bajo(evaluador):
    resultado = evaluador.evaluar_parametro("humedad", 10, 30, 60, "%")

    assert resultado.nombre == "humedad"
    assert resultado.estado.value == "BAJO"
    assert resultado.rango_min == 30
    assert resultado.rango_max == 60


def test_evaluador_parametro_optimo(evaluador):
    resultado = evaluador.evaluar_parametro("luz", 500, 300, 800, "lux")

    assert resultado.estado.value == "OPTIMO"
    assert resultado.valor == 500


def test_evaluador_parametro_alto(evaluador):
    resultado = evaluador.evaluar_parametro("temperatura", 35, 18, 28, "C")

    assert resultado.estado.value == "ALTO"
    assert resultado.unidad == "C"


def test_agregador_vitalidad_saludable(evaluador):
    resultados = [
        evaluador.evaluar_parametro("humedad", 45, 30, 60, "%"),
        evaluador.evaluar_parametro("luz", 500, 300, 800, "lux"),
        evaluador.evaluar_parametro("temperatura", 22, 18, 28, "C"),
    ]

    estado = evaluador.calcular_indice(resultados)

    assert estado.value == "SALUDABLE"


def test_diagnostico_retorna_en_riesgo_con_recomendacion_humedad_baja(referencia_sansevieria):
    diagnostico = DiagnosticarPlanta(
        referencia_sansevieria,
        EvaluadorPlanta(),
        Recomendador(),
    )

    resultado = diagnostico.ejecutar(Medicion("sansevieria", 10, 500, 22))

    assert resultado["estado"] == "EN_RIESGO"
    assert any("humedad" in recomendacion.lower() for recomendacion in resultado["recomendaciones"])


def test_diagnostico_critico_cuando_varios_parametros_fuera_de_rango(referencia_sansevieria):
    diagnostico = DiagnosticarPlanta(
        referencia_sansevieria,
        EvaluadorPlanta(),
        Recomendador(),
    )

    resultado = diagnostico.ejecutar(Medicion("sansevieria", 10, 900, 35))

    assert resultado["estado"] == "CRITICO"
    assert len(resultado["recomendaciones"]) >= 2


def test_diagnostico_lanza_error_si_especie_no_soportada(referencia_sansevieria):
    diagnostico = DiagnosticarPlanta(
        referencia_sansevieria,
        EvaluadorPlanta(),
        Recomendador(),
    )

    with pytest.raises(ValueError, match="ESPECIE_NO_SOPORTADA"):
        diagnostico.ejecutar(Medicion("orquidea", 50, 500, 22))
