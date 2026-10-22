import pytest

from app.application.use_cases.diagnosticar_planta import DiagnosticarPlanta
from app.domain.entities.medicion import Medicion
from app.domain.entities.rango_referencia import RangoReferencia
from app.domain.services.evaluador_planta import EvaluadorPlanta
from app.domain.services.recomendador import Recomendador
from app.domain.entities.lectura import Lectura
from app.domain.entities.planta import Planta
from app.domain.entities.especie import Especie
from app.domain.exceptions import AccesoDenegado, DatoInvalido
from app.domain.services.validador_de_estado import ValidadorDeEstado


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


class FakeTablaReferencia:
    def obtener_por_especie(self, especie):
        if especie.nombre == "sansevieria":
            return RangoReferencia("sansevieria", 30, 60, 300, 800, 18, 28)
        return None

    def listar_especies(self):
        return [Especie("sansevieria")]


def crear_lectura(humedad=45, luz=500, temperatura=22):
    from datetime import datetime, timezone

    return Lectura(
        especie=Especie("sansevieria"),
        humedad=humedad,
        luz=luz,
        temperatura=temperatura,
        marca_temporal=datetime.now(timezone.utc),
    )


def test_dominio_lectura_en_rango_con_doble_de_tabla():
    referencia = FakeTablaReferencia()
    validador = ValidadorDeEstado(EvaluadorPlanta(), Recomendador())

    resultado = validador.validar(
        crear_lectura(),
        referencia.obtener_por_especie(Especie("sansevieria")),
    )

    assert resultado.estado.value == "SALUDABLE"


def test_dominio_lectura_fuera_de_rango_es_un_estado_valido():
    referencia = FakeTablaReferencia()
    validador = ValidadorDeEstado(EvaluadorPlanta(), Recomendador())

    resultado = validador.validar(
        crear_lectura(humedad=10),
        referencia.obtener_por_especie(Especie("sansevieria")),
    )

    assert resultado.estado.value == "EN_RIESGO"
    assert resultado.parametros[0].estado.value == "BAJO"


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("humedad", "abc"), ("humedad", 101), ("luz", float("nan"))],
)
def test_dominio_rechaza_lecturas_invalidas(campo, valor):
    valores = {"humedad": 45, "luz": 500, "temperatura": 22}
    valores[campo] = valor

    with pytest.raises(DatoInvalido):
        crear_lectura(**valores)


def test_dominio_rechaza_lectura_de_planta_ajena():
    planta = Planta(
        id="planta-1",
        nombre="Potos",
        especie=Especie("potos"),
        propietario_id="usuario-1",
        dispositivo_id="esp32-1",
    )

    with pytest.raises(AccesoDenegado, match="PLANTA_NO_PERTENECE_AL_USUARIO"):
        planta.asegurar_propietario("usuario-2")
