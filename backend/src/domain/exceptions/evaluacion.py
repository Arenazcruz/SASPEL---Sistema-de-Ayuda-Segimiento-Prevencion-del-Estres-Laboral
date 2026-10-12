class EvaluacionError(Exception):
    def __init__(self, message, pendientes=()):
        super().__init__(message)
        self.pendientes = pendientes


class EvaluacionNoEncontrada(Exception):
    pass
