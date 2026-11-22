from django.utils import timezone
from src.domain.exceptions.resultados import ResultadoNoDisponible
from src.infrastructure.persistence.django.repositories.resultados import DjangoResultadosRepository


class DjangoPerfilRepository(DjangoResultadosRepository):
    def hoy(self):
        return timezone.localdate()

    def cuenta(self, actor):
        row=self.administration.users().get(pk=actor)
        if not getattr(row,'perfil_usuario',None):
            raise ResultadoNoDisponible('Solicita a Administración completar tu perfil institucional.')
        return row

    def consultar(self, actor):
        row=self.cuenta(actor); perfil=row.perfil_usuario
        return {k:getattr(row,k) for k in ('first_name','last_name','email')} | {
            k:getattr(perfil,k) for k in ('apellido_materno','telefono','fecha_nacimiento','sexo','codigo_empleado')
        } | {'area':perfil.area.nombre if perfil.area and not perfil.area.deleted else '',
             'cargo':perfil.cargo.nombre if perfil.cargo and not perfil.cargo.deleted else ''}

    def actualizar(self, actor, datos):
        row=self.cuenta(actor);perfil=row.perfil_usuario
        for name,value in datos.items():
            setattr(row if name in ('first_name','last_name') else perfil,name,value)
        row.actualizado_por=perfil.actualizado_por=str(actor)
        row.save(update_fields=['first_name','last_name','actualizado_por'])
        perfil.full_clean();perfil.save()
        return self.consultar(actor)
