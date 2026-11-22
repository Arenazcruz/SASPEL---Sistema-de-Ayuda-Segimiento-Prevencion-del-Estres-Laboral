from src.infrastructure.persistence.django.models import ReglaAlerta, Alerta, AccionAlerta, RangoInterpretacion
from src.infrastructure.persistence.django.repositories.resultados import DjangoResultadosRepository
from src.domain.services.alertas import validar_transicion_alerta
from src.domain.exceptions.resultados import ResultadoNoDisponible
from src.domain.exceptions.superadmin import AdministrationError

class DjangoAlertasRepository(DjangoResultadosRepository):
    def generar(self, resultado):
        row = self.resultados().filter(pk=resultado, rango__isnull=False).first()
        if row is None:
            return []
        rules = ReglaAlerta.objects.filter(rango_id=row.rango_id, activa=True, deleted=False, rango__deleted=False)
        return [Alerta.objects.get_or_create(regla=rule, resultado=row)[0].pk for rule in rules]

    def reglas(self, actor, datos=None, regla=None):
        if regla is not None:
            row = ReglaAlerta.objects.filter(pk=regla,deleted=False).first()
            if row is None: raise ResultadoNoDisponible('Regla no disponible.')
            row.activa=False; row.actualizado_por=str(actor); row.save(update_fields=['activa','actualizado_por'])
        elif datos is not None:
            if not RangoInterpretacion.objects.filter(pk=datos['rango_id'],activo=True,deleted=False,instrumento__deleted=False).exists():
                raise AdministrationError('Selecciona un rango configurado y disponible.')
            ReglaAlerta.objects.create(**datos,creado_por=str(actor),actualizado_por=str(actor))
        # Reglas inmutables: para cambiar nivel/rango se desactiva y se crea otra versión.
        return list(ReglaAlerta.objects.filter(deleted=False).values('id','nombre','rango_id','nivel','activa'))

    def autorizadas(self, actor):
        workers=self.vinculos(actor).values('trabajador_id')
        return Alerta.objects.filter(deleted=False,resultado_id__in=self.resultados().values('pk'),
            resultado__aplicacion__asignacion__trabajador_id__in=workers).select_related('regla','resultado__aplicacion__asignacion__trabajador').prefetch_related('acciones')

    def dto_alerta(self, row):
        user=row.resultado.aplicacion.asignacion.trabajador
        return {'id':row.pk,'trabajador_id':user.pk,'trabajador':user.get_full_name() or user.email,
            'origen':'RESULTADO','resultado_id':row.resultado_id,'regla_id':row.regla_id,'regla':row.regla.nombre,
            'nivel':row.regla.nivel,'estado':row.estado,'fecha':row.creado_en,
            'acciones':list(row.acciones.filter(deleted=False).values('id','estado','observacion','creado_en','creado_por'))}

    def listar_alertas(self, actor):
        return [self.dto_alerta(r) for r in self.autorizadas(actor)]

    def actuar(self, actor, alerta, datos):
        row=self.autorizadas(actor).filter(pk=alerta).first()
        if row is None: raise ResultadoNoDisponible('Alerta no disponible.')
        validar_transicion_alerta(row.estado,datos['estado'])
        AccionAlerta.objects.create(alerta=row,**datos,creado_por=str(actor),actualizado_por=str(actor))
        row.estado=datos['estado'];row.actualizado_por=str(actor);row.save(update_fields=['estado','actualizado_por'])
        return self.dto_alerta(row)
