from src.application.ports.output.perfil import PerfilRepository
from src.domain.exceptions.resultados import AccesoResultadosDenegado
from src.domain.exceptions.superadmin import AdministrationError
from src.domain.services.user_validation import validate_name, validate_phone, validate_birth_date


class GestionarPerfilPropio:
    def __init__(self, repository: PerfilRepository):
        self.repository = repository

    def ejecutar(self, actor, datos=None):
        with self.repository.atomic():
            if not self.repository.rol_activo(actor):
                raise AccesoResultadosDenegado('La cuenta no está disponible.')
            if datos is None:
                return self.repository.consultar(actor)
            permitidos={'first_name','last_name','apellido_materno','telefono','fecha_nacimiento','sexo'}
            if set(datos)-permitidos:
                raise AdministrationError('No puedes modificar campos institucionales desde tu perfil.')
            cambios=dict(datos)
            for name in ('first_name','last_name','apellido_materno'):
                if name in cambios:
                    cambios[name]=validate_name(cambios[name],name)
            if 'telefono' in cambios:
                cambios['telefono']=validate_phone(cambios['telefono'])
            if cambios.get('fecha_nacimiento'):
                validate_birth_date(cambios['fecha_nacimiento'],self.repository.hoy())
            if 'sexo' in cambios and cambios['sexo'] not in ('','F','M','O'):
                raise AdministrationError('Selecciona una opción de sexo válida.')
            return self.repository.actualizar(actor,cambios)
