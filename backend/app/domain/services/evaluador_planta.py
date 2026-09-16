from app.domain.entities.estado_parametro import EstadoParametro
from app.domain.entities.indice_vitalidad import IndiceVitalidad
from app.domain.entities.resultado_parametro import ResultadoParametro


class EvaluadorPlanta:

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

    def calcular_indice(self, resultados):

        fuera_de_rango = sum(
            1 for resultado in resultados
            if resultado.estado != EstadoParametro.OPTIMO
        )

        if fuera_de_rango == 0:
            return IndiceVitalidad.SALUDABLE

        if fuera_de_rango == 1:
            return IndiceVitalidad.EN_RIESGO

        return IndiceVitalidad.CRITICO
