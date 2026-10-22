class DominioError(Exception):
    pass


class DatoInvalido(DominioError):
    pass


class EspecieNoSoportada(DominioError):
    pass


class AccesoDenegado(DominioError):
    pass


class RecursoNoEncontrado(DominioError):
    pass


class DispositivoNoAutorizado(DominioError):
    pass
