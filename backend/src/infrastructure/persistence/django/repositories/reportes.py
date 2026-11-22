from django.db.models import Count
from django.db.models.functions import TruncDate
from src.infrastructure.persistence.django.models import InstrumentoPsicologico,AsignacionInstrumento,Cita,Seguimiento,AreaInstitucional
from src.infrastructure.persistence.django.repositories.resultados import DjangoResultadosRepository
from src.domain.exceptions.superadmin import AdministrationError

class DjangoReportesRepository(DjangoResultadosRepository):
    def consultar(self,actor,rol,tipo,filtros,exportar):
        profesional=rol=='PSICOLOGO';workers=self.vinculos(actor).values('trabajador_id')
        if tipo=='catalogos':
            areas=AreaInstitucional.objects.filter(deleted=False)
            instruments=InstrumentoPsicologico.objects.filter(deleted=False)
            if profesional:
                areas=areas.filter(pk__in=self.usuarios().filter(pk__in=workers).values('perfil_usuario__area_id'))
                instruments=instruments.filter(pk__in=AsignacionInstrumento.objects.filter(deleted=False,trabajador_id__in=workers).values('instrumento_id'))
            return {'areas':list(areas.order_by('nombre').values('id','nombre')),'instrumentos':list(instruments.order_by('nombre','version').values('id','nombre','version'))}
        estado=filtros.get('estado');area=filtros.get('area');fecha='creado_en'
        if tipo=='usuarios':
            rows=self.administration.users().filter(deleted=False).exclude(perfil_usuario__deleted=True)
            if profesional: rows=rows.filter(pk__in=workers)
            if area: rows=rows.filter(perfil_usuario__area_id=area)
            if estado:
                if estado not in ('ACTIVO','INACTIVO'): raise AdministrationError('Estado de usuario inválido.')
                rows=rows.filter(is_active=estado=='ACTIVO')
            fields=['first_name','last_name','email','functional_role','is_active','perfil_usuario__area__nombre']
            columns=['Nombre','Apellido','Correo','Rol','Activo','Área']
        elif tipo=='instrumentos':
            rows=InstrumentoPsicologico.objects.filter(deleted=False)
            if profesional: rows=rows.filter(pk__in=AsignacionInstrumento.objects.filter(deleted=False,trabajador_id__in=workers).values('instrumento_id'))
            if filtros.get('instrumento'): rows=rows.filter(pk=filtros['instrumento'])
            if estado:
                if estado not in ('ACTIVO','INACTIVO'): raise AdministrationError('Estado de instrumento inválido.')
                rows=rows.filter(activo=estado=='ACTIVO')
            fields=['codigo','nombre','version','activo'];columns=['Código','Instrumento','Versión','Activo']
        else:
            rows=(Cita if tipo=='citas' else Seguimiento).objects.filter(deleted=False,trabajador__deleted=False,trabajador__perfil_usuario__deleted=False)
            if profesional:
                rows=rows.filter(trabajador_id__in=workers)
                if tipo=='citas': rows=rows.filter(psicologo_id=actor)
            if area: rows=rows.filter(trabajador__perfil_usuario__area_id=area)
            if tipo=='citas':
                fecha='fecha_inicio'
                if estado and estado not in Cita.Estado.values: raise AdministrationError('Estado de cita inválido.')
            if estado: rows=rows.filter(estado=estado)
            if profesional:
                fields=['trabajador__email',fecha,'estado']
                columns=['Trabajador','Fecha','Estado']
                if tipo=='seguimiento': fields+=['proxima_revision'];columns+=['Próxima revisión']
        for key,lookup in [('desde','gte'),('hasta','lte')]:
            if filtros.get(key): rows=rows.filter(**{fecha+'__date__'+lookup:filtros[key]})
        if tipo in ('citas','seguimiento') and not profesional:
            # Administración recibe solo volúmenes operativos, nunca textos clínicos.
            rows=rows.annotate(dia=TruncDate(fecha))
            fields=['dia','estado'] if tipo=='citas' else ['dia']
            rows=rows.values(*fields).annotate(cantidad=Count('pk')).order_by(*fields)
            fields+=['cantidad'];columns=['Fecha','Estado','Cantidad'] if tipo=='citas' else ['Fecha','Cantidad de registros']
        else: rows=rows.order_by(fecha,'pk')
        total=rows.count();page=filtros.get('pagina',1)
        if exportar and total>10000: raise AdministrationError('Reduce el intervalo o los filtros para exportar hasta 10000 filas.')
        start=0 if exportar else (page-1)*50;end=total if exportar else start+50
        values=list(rows.values_list(*fields)[start:end]) if start < total else []
        return {'tipo':tipo,'columnas':columns,'filas':values,'total':total,'pagina':page,'por_pagina':50,'agregado':not profesional and tipo in ('citas','seguimiento')}
