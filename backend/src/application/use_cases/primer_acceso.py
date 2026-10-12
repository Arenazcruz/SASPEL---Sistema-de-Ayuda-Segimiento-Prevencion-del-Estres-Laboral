from src.application.dto.primer_acceso import EstadoPrimerAcceso
from src.application.ports.input.primer_acceso import PrimerAcceso
from src.application.ports.output.primer_acceso import PrimerAccesoRepository
from src.application.use_cases.superadmin import validate_password
from src.domain.exceptions.primer_acceso import PrimerAccesoError
from src.domain.services.primer_acceso import ROLES_POLITICAS


class GestionarPrimerAcceso(PrimerAcceso):
    def __init__(self, repository: PrimerAccesoRepository):
        self.repository = repository

    def _vigentes(self):
        ahora = self.repository.ahora()
        return [p for p in self.repository.politicas()
                if p.activo and p.obligatoria and p.vigente_desde <= ahora]

    def pendientes(self, usuario_id):
        if self.repository.cuenta(usuario_id).role not in ROLES_POLITICAS:
            return []
        aceptadas = self.repository.aceptadas(usuario_id)
        return [p for p in self._vigentes() if p.id not in aceptadas]

    def estado(self, usuario_id):
        cuenta = self.repository.cuenta(usuario_id)
        password = cuenta.role in ROLES_POLITICAS and cuenta.debe_cambiar_password
        pendientes = tuple(p.id for p in self.pendientes(usuario_id))
        ruta = ('/primer-acceso/password' if password else
                '/primer-acceso/politicas' if pendientes else cuenta.dashboard_path)
        return EstadoPrimerAcceso(password, pendientes, not password and not pendientes, ruta)

    def cambiar_password(self, command):
        with self.repository.atomic(command.usuario_id):
            if not self.estado(command.usuario_id).debe_cambiar_password:
                raise PrimerAccesoError('No hay un cambio de contraseña temporal pendiente.')
            validate_password(command.password, command.password_confirmation)
            self.repository.cambiar_password(command.usuario_id, command.password)
            return self.estado(command.usuario_id)

    def aceptar(self, command):
        with self.repository.atomic(command.usuario_id):
            if self.estado(command.usuario_id).debe_cambiar_password:
                raise PrimerAccesoError('Primero debes cambiar tu contraseña temporal.')
            if self.repository.cuenta(command.usuario_id).role not in ROLES_POLITICAS:
                raise PrimerAccesoError('Esta cuenta no requiere aceptar políticas.')
            solicitadas = set(command.politicas)
            vigentes = {p.id for p in self._vigentes()}
            if not solicitadas or not solicitadas <= vigentes:
                raise PrimerAccesoError('Las políticas cambiaron. Recarga y revisa las versiones vigentes.', 'politicas')
            self.repository.aceptar(command.usuario_id, solicitadas)
            return self.estado(command.usuario_id)
