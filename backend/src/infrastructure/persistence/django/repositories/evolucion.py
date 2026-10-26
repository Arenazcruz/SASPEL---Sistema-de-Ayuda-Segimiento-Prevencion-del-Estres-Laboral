from src.infrastructure.persistence.django.repositories.resultados import DjangoResultadosRepository


class DjangoEvolucionRepository(DjangoResultadosRepository):
    def puntos(self, trabajador, filtros):
        rows = self.resultados().filter(aplicacion__asignacion__trabajador_id=trabajador,
                                       aplicacion__asignacion__estado='COMPLETADA')
        if filtros.get('desde'):
            rows = rows.filter(fecha_historial__date__gte=filtros['desde'])
        if filtros.get('hasta'):
            rows = rows.filter(fecha_historial__date__lte=filtros['hasta'])
        if filtros.get('instrumento_id'):
            rows = rows.filter(aplicacion__asignacion__instrumento_id=filtros['instrumento_id'])
        return [dict(resultado_id=r.pk, instrumento_id=r.aplicacion.asignacion.instrumento_id,
                     nombre=r.aplicacion.asignacion.instrumento.nombre,
                     version=r.aplicacion.asignacion.instrumento.version, fecha=r.fecha_historial,
                     puntaje=str(r.puntaje_total), nivel=r.rango.nombre if r.rango else None)
                for r in rows.order_by('fecha_historial', 'pk')]
