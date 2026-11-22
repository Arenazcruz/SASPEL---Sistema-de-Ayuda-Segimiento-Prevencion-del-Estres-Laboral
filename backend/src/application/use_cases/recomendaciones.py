from src.application.ports.output.recomendaciones import RecomendacionesRepository
from src.domain.exceptions.resultados import AccesoResultadosDenegado, ResultadoNoDisponible
from src.domain.exceptions.superadmin import AdministrationError


class GestionarRecomendaciones:
    def __init__(self, repository: RecomendacionesRepository):
        self.repository = repository

    def propias(self, actor):
        if self.repository.rol_activo(actor) != "TRABAJADOR":
            raise AccesoResultadosDenegado("Solo para el trabajador.")
        return self.repository.compartidas(actor)

    def ejecutar(self, actor, seguimiento, datos=None, recomendacion=None):
        with self.repository.atomic():
            if self.repository.rol_activo(actor) != 'PSICOLOGO':
                raise AccesoResultadosDenegado('Solo el profesional autorizado puede gestionar recomendaciones.')
            trabajador = self.repository.trabajador_seguimiento(seguimiento)
            if not trabajador or not self.repository.tiene_asignacion_activa(actor, trabajador):
                raise ResultadoNoDisponible('El seguimiento no está disponible.')
            if recomendacion is not None:
                row = self.repository.obtener(seguimiento, recomendacion)
                if not row:
                    raise ResultadoNoDisponible('La recomendación no está disponible.')
                estado = datos['estado']
                permitidos = {'PENDIENTE': {'EN_PROGRESO', 'COMPLETADA', 'CANCELADA'}, 'EN_PROGRESO': {'COMPLETADA', 'CANCELADA'}}
                if estado not in permitidos.get(row['estado'], set()):
                    raise AdministrationError('La recomendación ya cambió de estado o está cerrada.')
                return self.repository.cambiar(actor, recomendacion, estado)
            if datos is not None:
                texto = datos['texto'].strip()
                if not texto or len(texto) > 5000:
                    raise AdministrationError('Escribe una recomendación de hasta 5000 caracteres.')
                return self.repository.crear(actor, seguimiento, texto, datos.get("compartida", False))
            return self.repository.listar(seguimiento)
