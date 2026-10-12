"""Carga los nombres institucionales solicitados sin reemplazar registros existentes."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from src.infrastructure.persistence.django.models import AreaCargo, AreaInstitucional, CargoInstitucional


AREAS = (
    'Área de Negocios',
    'Área de Servicios de Desarrollo',
    'Área de Recursos Humanos',
    'Área de Operaciones',
    'Área de Finanzas y Captaciones',
    'Área de Planificación e Innovación',
    'Área de TIC',
    'Área de Riesgos',
    'Área Legal',
    'Área de Administración',
    'Área de Auditoría Interna',
    'Área de Imagen y Comunicación',
    'Gerencia General',
)

CARGOS = (
    'ADMINISTRADOR DE SISTEMAS',
    'ANALISTA DE ADMINISTRACION',
    'ANALISTA DE ALMACENES',
    'ANALISTA DE BASE DE DATOS Y GESTION DE USUARIOS',
    'ANALISTA DE CALIDAD Y PROCESOS',
    'ANALISTA DE CIENCIA DE DATOS',
    'ANALISTA DE CONTABILIDAD 2',
    'ANALISTA DE CONTRATACIONES',
    'ANALISTA DE CREDITOS DE OFICINA NACIONAL',
    'ANALISTA DE CUMPLIMIENTO',
    'ANALISTA DE DATOS E INFORMACION GERENCIAL',
    'ANALISTA DE GESTION DE INFORMACION',
    'ANALISTA DE GESTION DE LIQUIDEZ',
    'ANALISTA DE GESTION DE RECURSOS HUMANOS',
    'ANALISTA DE GESTION DE SISTEMAS',
    'ANALISTA DE IMAGEN Y COMUNICACION',
    'ANALISTA DE IMPUESTOS',
    'ANALISTA DE INFRAESTRUCTURA TECNOLOGICA',
    'ANALISTA DE INVESTIGACION E INNOVACION',
    'ANALISTA DE NEGOCIOS',
    'ANALISTA DE NORMAS Y CONTRATOS',
    'ANALISTA DE PASIVOS E INVERSIONES',
    'ANALISTA DE PLANIFICACION E INNOVACION',
    'ANALISTA DE PROCEDIMIENTOS LEGALES',
    'ANALISTA DE REDES Y COMUNICACIONES',
    'ANALISTA DE SEGURIDAD Y SALUD EN EL TRABAJO',
    'ANALISTA DE SERVICIOS DE DESARROLLO',
    'ANALISTA DE SERVIDORES Y SISTEMAS OPERATIVOS',
    'ANALISTA OPERATIVO DE CAPTACIONES',
    'ASISTENTE COMERCIAL DE CAPTACIONES',
    'ASISTENTE DE ADMINISTRACION DE RRHH',
    'ASISTENTE DE ARCHIVOS',
    'ASISTENTE DE CAPACITACION',
    'ASISTENTE DE CONTABILIDAD',
    'ASISTENTE DE CONTABILIDAD OFICINA CENTRAL',
    'ASISTENTE DE IMPUESTOS',
    'ASISTENTE DE NEGOCIOS',
    'ASISTENTE DE OPERACIONES',
    'ASISTENTE DE RETENCIONES',
    'ASISTENTE DE RETENCIONES JUDICIALES',
    'ASISTENTE DE RIESGO TECNOLOGICO',
    'ASISTENTE DE SEGURIDAD FISICA',
    'ASISTENTE DE SERVICIOS DE DESARROLLO',
    'ASISTENTE OPERATIVO DE CAPTACIONES',
    'AUDITOR INTERNO',
    'AUXILIAR DE CUMPLIMIENTO',
    'AUXILIAR DE GESTION DE RECURSOS HUMANOS',
    'AUXILIAR DE MANTENIMIENTO Y ALMACENES',
    'AUXILIAR DE OPERACIONES Y SEGUROS (PUNTO DE RECLAMO)',
    'AUXILIAR DE OPERACIONES Y SERVICIOS AUXILIARES',
    'AUXILIAR DE SEGURIDAD Y SALUD EN EL TRABAJO',
    'AUXILIAR DE SOPORTE TECNICO',
    'CONTADOR OFICINA CENTRAL',
    'FACILITADOR NACIONAL DE CAPACITACION',
    'FUNCIONARIO RESPONSABLE',
    'GERENTE GENERAL',
    'GERENTE NACIONAL DE AUDITORIA INTERNA',
    'GERENTE NACIONAL DE FINANZAS Y CAPTACIONES',
    'GERENTE NACIONAL DE NEGOCIOS',
    'GERENTE NACIONAL DE OPERACIONES',
    'GERENTE NACIONAL DE PLANIFICACION E INNOVACION',
    'GERENTE NACIONAL DE RECURSOS HUMANOS',
    'GERENTE NACIONAL DE RIESGOS',
    'GERENTE NACIONAL DE SERVICIOS DE DESARROLLO',
    'GERENTE NACIONAL DE TECNOLOGIA DE INFORMACION',
    'GERENTE NACIONAL LEGAL',
    'JEFE DE AUDITORIA INTERNA',
    'JEFE DE RIESGOS',
    'JEFE DE RIESGOS DE SUCURSAL',
    'JEFE EN ANALISIS DE DATOS',
    'JEFE NACIONAL COMERCIAL DE CAPTACIONES',
    'JEFE NACIONAL DE ADMINISTRACION',
    'JEFE NACIONAL DE ADMINISTRACION DE RECURSOS HUMANOS',
    'JEFE NACIONAL DE AUDITORIA INTERNA',
    'JEFE NACIONAL DE BANCA COMUNAL',
    'JEFE NACIONAL DE CALIDAD Y PROCESOS',
    'JEFE NACIONAL DE CAPACITACION',
    'JEFE NACIONAL DE CONTABILIDAD',
    'JEFE NACIONAL DE CONTROL DE CALIDAD',
    'JEFE NACIONAL DE CREDITO INDIVIDUAL',
    'JEFE NACIONAL DE GESTION CREDITICIA',
    'JEFE NACIONAL DE GESTION DE PROYECTOS SOCIALES',
    'JEFE NACIONAL DE GESTION DE RECURSOS HUMANOS',
    'JEFE NACIONAL DE GESTION DE SISTEMAS',
    'JEFE NACIONAL DE INGENIERIA DE DATOS',
    'JEFE NACIONAL DE NORMAS Y CONTRATOS',
    'JEFE NACIONAL DE OPERACIONES',
    'JEFE NACIONAL DE PLANIFICACION E INNOVACION',
    'JEFE NACIONAL DE PROCEDIMIENTOS LEGALES',
    'JEFE NACIONAL DE PROMOCION SOCIAL',
    'JEFE NACIONAL DE REDES Y COMUNICACIONES',
    'JEFE NACIONAL DE RIESGO CREDITICIO',
    'JEFE NACIONAL DE RIESGO DE LIQUIDEZ Y DE MERCADO',
    'JEFE NACIONAL DE RIESGO INTEGRAL',
    'JEFE NACIONAL DE RIESGO OPERACIONAL',
    'JEFE NACIONAL DE RIESGO TECNOLOGICO',
    'JEFE NACIONAL DE SEGURIDAD FISICA',
    'JEFE NACIONAL DE SERVICIOS EDUCATIVOS',
    'JEFE NACIONAL DE SERVICIOS FINANCIEROS AUXILIARES',
    'JEFE NACIONAL DE SERVIDORES Y BASES DE DATOS',
    'JEFE NACIONAL DE SUPERVISION NORMATIVA',
    'JEFE NACIONAL DE TESORERIA',
    'JEFE NACIONAL OPERATIVO DE CAPTACIONES',
    'MENSAJERIA Y LIMPIEZA OFICINA NACIONAL',
    'MENSAJERO',
    'MENSAJERO OFICINA NACIONAL 2',
    'SECRETARIA OFICINA NACIONAL',
    'SUB GERENTE NACIONAL DE CONTABILIDAD',
    'SUB GERENTE NACIONAL DE FINANZAS Y CAPTACIONES',
    'SUB GERENTE NACIONAL DE IMAGEN Y COMUNICACION',
    'SUB GERENTE NACIONAL DE NEGOCIOS',
)


AREA_ALIASES = {
    'Área de Recursos Humanos': 'Área de Recursos Humanos.',
    'Área de Operaciones': 'Área de operaciones',
    'Área de Finanzas y Captaciones': 'Área de finanzas y captaciones',
    'Área de Planificación e Innovación': 'Área de planificación e innovación',
    'Área de TIC': 'Area de TIC',
    'Área Legal': 'Área legal',
}

AREA_CARGOS = {
    'Área de Negocios': (
        'ANALISTA DE CREDITOS DE OFICINA NACIONAL',
        'ANALISTA DE NEGOCIOS',
        'ASISTENTE DE NEGOCIOS',
        'GERENTE NACIONAL DE NEGOCIOS',
        'JEFE NACIONAL DE BANCA COMUNAL',
        'JEFE NACIONAL DE CREDITO INDIVIDUAL',
        'JEFE NACIONAL DE GESTION CREDITICIA',
        'SUB GERENTE NACIONAL DE NEGOCIOS',
    ),
    'Área de Servicios de Desarrollo': (
        'ANALISTA DE SERVICIOS DE DESARROLLO',
        'ASISTENTE DE SERVICIOS DE DESARROLLO',
        'GERENTE NACIONAL DE SERVICIOS DE DESARROLLO',
        'JEFE NACIONAL DE GESTION DE PROYECTOS SOCIALES',
        'JEFE NACIONAL DE PROMOCION SOCIAL',
        'JEFE NACIONAL DE SERVICIOS EDUCATIVOS',
    ),
    'Área de Recursos Humanos': (
        'ANALISTA DE GESTION DE RECURSOS HUMANOS',
        'ANALISTA DE SEGURIDAD Y SALUD EN EL TRABAJO',
        'ASISTENTE DE ADMINISTRACION DE RRHH',
        'ASISTENTE DE CAPACITACION',
        'AUXILIAR DE GESTION DE RECURSOS HUMANOS',
        'AUXILIAR DE SEGURIDAD Y SALUD EN EL TRABAJO',
        'FACILITADOR NACIONAL DE CAPACITACION',
        'GERENTE NACIONAL DE RECURSOS HUMANOS',
        'JEFE NACIONAL DE ADMINISTRACION DE RECURSOS HUMANOS',
        'JEFE NACIONAL DE CAPACITACION',
        'JEFE NACIONAL DE GESTION DE RECURSOS HUMANOS',
    ),
    'Área de Operaciones': (
        'ASISTENTE DE OPERACIONES',
        'AUXILIAR DE OPERACIONES Y SEGUROS (PUNTO DE RECLAMO)',
        'AUXILIAR DE OPERACIONES Y SERVICIOS AUXILIARES',
        'GERENTE NACIONAL DE OPERACIONES',
        'JEFE NACIONAL DE OPERACIONES',
        'JEFE NACIONAL DE SERVICIOS FINANCIEROS AUXILIARES',
    ),
    'Área de Finanzas y Captaciones': (
        'ANALISTA DE CONTABILIDAD 2',
        'ANALISTA DE GESTION DE LIQUIDEZ',
        'ANALISTA DE IMPUESTOS',
        'ANALISTA DE PASIVOS E INVERSIONES',
        'ANALISTA OPERATIVO DE CAPTACIONES',
        'ASISTENTE COMERCIAL DE CAPTACIONES',
        'ASISTENTE DE CONTABILIDAD',
        'ASISTENTE DE CONTABILIDAD OFICINA CENTRAL',
        'ASISTENTE DE IMPUESTOS',
        'ASISTENTE DE RETENCIONES',
        'ASISTENTE OPERATIVO DE CAPTACIONES',
        'CONTADOR OFICINA CENTRAL',
        'GERENTE NACIONAL DE FINANZAS Y CAPTACIONES',
        'JEFE NACIONAL COMERCIAL DE CAPTACIONES',
        'JEFE NACIONAL DE CONTABILIDAD',
        'JEFE NACIONAL DE TESORERIA',
        'JEFE NACIONAL OPERATIVO DE CAPTACIONES',
        'SUB GERENTE NACIONAL DE CONTABILIDAD',
        'SUB GERENTE NACIONAL DE FINANZAS Y CAPTACIONES',
    ),
    'Área de Planificación e Innovación': (
        'ANALISTA DE CALIDAD Y PROCESOS',
        'ANALISTA DE CIENCIA DE DATOS',
        'ANALISTA DE DATOS E INFORMACION GERENCIAL',
        'ANALISTA DE GESTION DE INFORMACION',
        'ANALISTA DE INVESTIGACION E INNOVACION',
        'ANALISTA DE PLANIFICACION E INNOVACION',
        'GERENTE NACIONAL DE PLANIFICACION E INNOVACION',
        'JEFE EN ANALISIS DE DATOS',
        'JEFE NACIONAL DE CALIDAD Y PROCESOS',
        'JEFE NACIONAL DE CONTROL DE CALIDAD',
        'JEFE NACIONAL DE PLANIFICACION E INNOVACION',
    ),
    'Área de TIC': (
        'ADMINISTRADOR DE SISTEMAS',
        'ANALISTA DE BASE DE DATOS Y GESTION DE USUARIOS',
        'ANALISTA DE GESTION DE SISTEMAS',
        'ANALISTA DE INFRAESTRUCTURA TECNOLOGICA',
        'ANALISTA DE REDES Y COMUNICACIONES',
        'ANALISTA DE SERVIDORES Y SISTEMAS OPERATIVOS',
        'AUXILIAR DE SOPORTE TECNICO',
        'GERENTE NACIONAL DE TECNOLOGIA DE INFORMACION',
        'JEFE NACIONAL DE GESTION DE SISTEMAS',
        'JEFE NACIONAL DE INGENIERIA DE DATOS',
        'JEFE NACIONAL DE REDES Y COMUNICACIONES',
        'JEFE NACIONAL DE SERVIDORES Y BASES DE DATOS',
    ),
    'Área de Riesgos': (
        'ANALISTA DE CUMPLIMIENTO',
        'ASISTENTE DE RIESGO TECNOLOGICO',
        'ASISTENTE DE SEGURIDAD FISICA',
        'AUXILIAR DE CUMPLIMIENTO',
        'GERENTE NACIONAL DE RIESGOS',
        'JEFE DE RIESGOS',
        'JEFE DE RIESGOS DE SUCURSAL',
        'JEFE NACIONAL DE RIESGO CREDITICIO',
        'JEFE NACIONAL DE RIESGO DE LIQUIDEZ Y DE MERCADO',
        'JEFE NACIONAL DE RIESGO INTEGRAL',
        'JEFE NACIONAL DE RIESGO OPERACIONAL',
        'JEFE NACIONAL DE RIESGO TECNOLOGICO',
        'JEFE NACIONAL DE SEGURIDAD FISICA',
        'JEFE NACIONAL DE SUPERVISION NORMATIVA',
    ),
    'Área Legal': (
        'ANALISTA DE NORMAS Y CONTRATOS',
        'ANALISTA DE PROCEDIMIENTOS LEGALES',
        'ASISTENTE DE RETENCIONES JUDICIALES',
        'GERENTE NACIONAL LEGAL',
        'JEFE NACIONAL DE NORMAS Y CONTRATOS',
        'JEFE NACIONAL DE PROCEDIMIENTOS LEGALES',
    ),
    'Área de Administración': (
        'ANALISTA DE ADMINISTRACION',
        'ANALISTA DE ALMACENES',
        'ANALISTA DE CONTRATACIONES',
        'ASISTENTE DE ARCHIVOS',
        'AUXILIAR DE MANTENIMIENTO Y ALMACENES',
        'JEFE NACIONAL DE ADMINISTRACION',
        'MENSAJERIA Y LIMPIEZA OFICINA NACIONAL',
        'MENSAJERO',
        'MENSAJERO OFICINA NACIONAL 2',
    ),
    'Área de Auditoría Interna': (
        'AUDITOR INTERNO',
        'GERENTE NACIONAL DE AUDITORIA INTERNA',
        'JEFE DE AUDITORIA INTERNA',
        'JEFE NACIONAL DE AUDITORIA INTERNA',
    ),
    'Área de Imagen y Comunicación': (
        'ANALISTA DE IMAGEN Y COMUNICACION',
        'SUB GERENTE NACIONAL DE IMAGEN Y COMUNICACION',
    ),
    'Gerencia General': (
        'GERENTE GENERAL',
        'FUNCIONARIO RESPONSABLE',
        'SECRETARIA OFICINA NACIONAL',
    ),
}


class Command(BaseCommand):
    help = 'Normaliza 13 áreas, conserva 111 cargos y carga sus 111 relaciones principales.'

    def handle(self, *args, **options):
        results = []
        with transaction.atomic():
            # Renombrar conserva UUID, perfiles, descripción y auditoría de creación.
            for canonical, previous in AREA_ALIASES.items():
                matches = list(AreaInstitucional.objects.select_for_update().filter(nombre__in=[canonical, previous]))
                if len(matches) > 1:
                    raise CommandError(f'Existen ambas áreas: {canonical} / {previous}. No se fusionaron ni borraron registros.')
                if matches and matches[0].nombre != canonical:
                    item = matches[0]
                    item.nombre = canonical
                    item.actualizado_por = 'SYSTEM'
                    item.save(update_fields=['nombre', 'actualizado_por'])
            for label, model, names in (
                ('Áreas', AreaInstitucional, AREAS),
                ('Cargos', CargoInstitucional, CARGOS),
            ):
                created_count = updated_count = 0
                for name in names:
                    item, created = model.objects.select_for_update().get_or_create(
                        nombre=name,
                        defaults={'activo': True, 'deleted': False, 'descripcion': ''},
                    )
                    if created:
                        created_count += 1
                    elif not item.activo or item.deleted:
                        item.activo = True
                        item.deleted = False
                        item.actualizado_por = 'SYSTEM'
                        item.save(update_fields=['activo', 'deleted', 'actualizado_por'])
                        updated_count += 1
                results.append(
                    f'{label}: {len(names)} presentes; {created_count} creados, '
                    f'{updated_count} reactivados, {len(names) - created_count - updated_count} conservados.'
                )
            areas = {item.nombre: item for item in AreaInstitucional.objects.filter(nombre__in=AREAS)}
            cargos = {item.nombre: item for item in CargoInstitucional.objects.filter(nombre__in=CARGOS)}
            created_count = restored_count = 0
            for area, names in AREA_CARGOS.items():
                for name in names:
                    relation, created = AreaCargo.objects.select_for_update().get_or_create(
                        area=areas[area], cargo=cargos[name], defaults={'deleted': False},
                    )
                    if created:
                        created_count += 1
                    elif relation.deleted:
                        relation.deleted = False
                        relation.actualizado_por = 'SYSTEM'
                        relation.save(update_fields=['deleted', 'actualizado_por'])
                        restored_count += 1
            results.append(f'AreaCargo: 111 relaciones principales; {created_count} creadas, {restored_count} restauradas.')
        for result in results:
            self.stdout.write(self.style.SUCCESS(result))
