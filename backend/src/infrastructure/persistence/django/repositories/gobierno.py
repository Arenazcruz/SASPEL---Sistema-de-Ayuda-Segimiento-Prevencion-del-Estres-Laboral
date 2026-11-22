from django.core.exceptions import ValidationError
from django.utils import timezone
from src.domain.exceptions.superadmin import AdministrationError
from src.infrastructure.persistence.django.models import PoliticaSistema, EventoAuditoria
from src.infrastructure.persistence.django.repositories.resultados import DjangoResultadosRepository


class DjangoGobiernoRepository(DjangoResultadosRepository):
    @staticmethod
    def politica(row):
        return {k: getattr(row, k) for k in ('id', 'tipo', 'titulo', 'version', 'contenido', 'vigente_desde', 'obligatoria', 'activo')}

    def politicas(self):
        return [self.politica(r) for r in PoliticaSistema.objects.filter(deleted=False).order_by('-vigente_desde', '-pk')]

    def publicar(self, actor, datos):
        if PoliticaSistema.objects.filter(tipo=datos['tipo'], version=datos['version']).exists():
            raise AdministrationError('Esta versión ya existe. Publica una versión nueva.')
        # Bloquea las versiones también frente al registro concurrente de aceptaciones.
        anteriores = list(PoliticaSistema.objects.select_for_update().filter(tipo=datos['tipo']).order_by('pk'))
        for row in anteriores:
            if row.activo:
                row.activo=False; row.actualizado_por=str(actor)
                row.save(update_fields=['activo', 'actualizado_por'])
        try:
            row = PoliticaSistema.objects.create(**datos, activo=True, vigente_desde=timezone.now(), creado_por=str(actor), actualizado_por=str(actor))
        except ValidationError:
            raise AdministrationError('Revisa los datos de la nueva política.') from None
        return self.politica(row)

    def auditoria(self, actor, rol, filtros):
        rows = EventoAuditoria.objects.all()
        if rol == 'ADMIN':
            # Institución única: consulta sus operaciones administrativas sin
            # revelar entidades clínicas ni auditoría global reservada al SA.
            rows = rows.filter(actor_id=actor, entidad__in=['areainstitucional','cargoinstitucional','areacargo','tipofactorpsicosocial','usuario','perfilusuario','instrumentopsicologico','preguntainstrumento','escalarespuesta','opcionrespuesta','rangointerpretacion','asignacionprofesional'])
        for key, lookup in [('desde','fecha__date__gte'),('hasta','fecha__date__lte'),('actor_id','actor_id'),('entidad','entidad'),('accion','accion')]:
            if filtros.get(key):
                rows = rows.filter(**{lookup: filtros[key]})
        count=rows.count(); page=filtros.get('page',1); start=(page-1)*50
        items=list(rows.values('id','actor_id','fecha','accion','entidad','entidad_id','estado')[start:start+50]) if start<count else []
        return {'count':count,'page':page,'page_size':50,'results':items}
