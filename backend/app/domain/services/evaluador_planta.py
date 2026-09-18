from app.domain.entities.estado_parametro import EstadoParametro
from app.domain.entities.indice_vitalidad import IndiceVitalidad
from app.domain.entities.resultado_parametro import ResultadoParametro


class AgregadorVitalidad:

    def calcular(self, resultados):
        fuera_de_rango = sum(
            1 for resultado in resultados
            if resultado.estado != EstadoParametro.OPTIMO
        )

        if fuera_de_rango == 0:
            return IndiceVitalidad.SALUDABLE

        if fuera_de_rango == 1:
            return IndiceVitalidad.EN_RIESGO

        return IndiceVitalidad.CRITICO


class EvaluadorPlanta:

    def __init__(self, agregador=None):
        self.agregador = agregador or AgregadorVitalidad()

    def evaluar_parametro(
        self,
        nombre,
        valor,
        minimo,
        maximo,
        unidad
    ):
        if valor < minimo:
            estado = EstadoParametro.BAJO
        elif valor > maximo:
            estado = EstadoParametro.ALTO
        else:
            estado = EstadoParametro.OPTIMO

        return ResultadoParametro(
            nombre,
            valor,
            unidad,
            minimo,
            maximo,
            estado
        )

    def evaluar_parametros(self, configuracion_parametros):
        resultados = []

        for parametro in configuracion_parametros:
            resultados.append(
                self.evaluar_parametro(
                    parametro["nombre"],
                    parametro["valor"],
                    parametro["minimo"],
                    parametro["maximo"],
                    parametro["unidad"],
                )
            )

        return resultados

    def calcular_indice(self, resultados, agregador=None):
        estrategia = agregador or self.agregador
        return estrategia.calcular(resultados)
