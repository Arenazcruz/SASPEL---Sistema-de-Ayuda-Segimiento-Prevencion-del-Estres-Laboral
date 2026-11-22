from src.application.ports.output.resultados import ResultadosRepository
from src.domain.exceptions.resultados import AccesoResultadosDenegado, ResultadoNoDisponible


class ConsultarResultados:
    def __init__(self, repository: ResultadosRepository):
        self.repository = repository

    def exigir_rol(self, usuario_id, role):
        if self.repository.rol_activo(usuario_id) != role:
            raise AccesoResultadosDenegado('No tienes permiso para consultar esta información.')

    def autorizar_trabajador(self, psicologo_id, trabajador_id):
        # La existencia de una relación histórica no concede acceso clínico actual.
        if not self.repository.tiene_asignacion_activa(psicologo_id, trabajador_id):
            raise ResultadoNoDisponible('La información solicitada no está disponible.')

    def buscar(self, resultado_id):
        record = self.repository.resultado(resultado_id)
        if record is None:
            raise ResultadoNoDisponible('La información solicitada no está disponible.')
        return record

    def propios(self, usuario_id):
        with self.repository.atomic():
            self.exigir_rol(usuario_id, 'TRABAJADOR')
            return self.repository.listar_resultados(usuario_id)

    def detalle_propio(self, usuario_id, resultado_id):
        with self.repository.atomic():
            self.exigir_rol(usuario_id, 'TRABAJADOR')
            owner, result = self.buscar(resultado_id)
            if owner != usuario_id:
                raise ResultadoNoDisponible('La información solicitada no está disponible.')
            return result

    def trabajadores(self, psicologo_id):
        with self.repository.atomic():
            self.exigir_rol(psicologo_id, 'PSICOLOGO')
            return self.repository.trabajadores(psicologo_id)

    def de_trabajador(self, psicologo_id, trabajador_id):
        with self.repository.atomic():
            self.exigir_rol(psicologo_id, 'PSICOLOGO')
            self.autorizar_trabajador(psicologo_id, trabajador_id)
            return self.repository.listar_resultados(trabajador_id)

    def detalle_profesional(self, psicologo_id, resultado_id):
        with self.repository.atomic():
            self.exigir_rol(psicologo_id, 'PSICOLOGO')
            owner, result = self.buscar(resultado_id)
            self.autorizar_trabajador(psicologo_id, owner)
            return result
