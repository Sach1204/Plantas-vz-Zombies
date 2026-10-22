from app.domain.entities.diagnostico import Diagnostico
from app.domain.entities.estado import Estado
from app.domain.exceptions import EspecieNoSoportada


class ValidadorDeEstado:
    def __init__(self, evaluador, recomendador):
        self.evaluador = evaluador
        self.recomendador = recomendador

    def validar(self, lectura, referencia):
        if referencia is None:
            raise EspecieNoSoportada("ESPECIE_NO_SOPORTADA")

        resultados = self.evaluador.evaluar_parametros(
            referencia.obtener_parametros(lectura)
        )
        indice = self.evaluador.calcular_indice(resultados)
        recomendaciones = tuple(
            recomendacion
            for resultado in resultados
            if (recomendacion := self.recomendador.generar(resultado))
        )
        return Diagnostico(
            especie=lectura.especie.nombre,
            estado=Estado(indice.value),
            parametros=tuple(resultados),
            recomendaciones=recomendaciones,
        )
