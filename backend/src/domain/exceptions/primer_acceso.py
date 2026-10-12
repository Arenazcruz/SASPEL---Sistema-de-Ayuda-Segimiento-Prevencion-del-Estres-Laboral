class PrimerAccesoError(Exception):
    def __init__(self, message, field='detail'):
        super().__init__(message)
        self.field = field
