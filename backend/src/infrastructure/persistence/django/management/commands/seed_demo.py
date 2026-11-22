"""Datos sintéticos para una BD exclusiva de demostración de SASPEL."""
import os
from datetime import time, timedelta
from uuid import NAMESPACE_URL, uuid5
from zoneinfo import ZoneInfo

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from src.application.use_cases.evaluacion_inicial import AsignarEvaluacionInicial
from src.infrastructure.persistence.django.repositories.administration import DjangoAdministrationRepository
from src.infrastructure.persistence.django import models as m


ROLES = {'sa':'SUPERADMIN', 'admin':'ADMIN', 'psi':'PSICOLOGO',
         'nuevo':'NUEVO_TRABAJADOR', 'trab':'TRABAJADOR'}


def clave(model, key):
    return uuid5(NAMESPACE_URL, f'urn:saspel:demo:h4:{model._meta.label_lower}:{key}')


def registro(model, key, **data):
    return model.objects.get_or_create(pk=clave(model, key), defaults=data)[0]


class Command(BaseCommand):
    help = 'Prepara cinco cuentas y un caso longitudinal en saspel_demo_h4.'

    @transaction.atomic
    def handle(self, *args, **options):
        with connection.cursor() as cur:
            cur.execute('SELECT current_database()')
            database = cur.fetchone()[0]
        isolated = os.getenv('SASPEL_ISOLATED') == '1' and database in {
            'saspel_verificacion','test_saspel_verificacion'}
        if database != 'saspel_demo_h4' and not isolated:
            raise CommandError('Usa una base dedicada con nombre saspel_demo_h4.')
        password = os.getenv('SASPEL_DEMO_PASSWORD', '')
        if len(password) < 12:
            raise CommandError('Define SASPEL_DEMO_PASSWORD con al menos 12 caracteres.')
        if m.Usuario.objects.exclude(pk__in=[clave(m.Usuario,k) for k in ROLES]).exists():
            raise CommandError('La base contiene cuentas ajenas al dataset.')
        call_command('seed_initial_instrument',stdout=self.stdout)
        area = registro(m.AreaInstitucional,'area',nombre='Operaciones demo')
        cargo = registro(m.CargoInstitucional,'cargo',nombre='Auxiliar demo')
        registro(m.AreaCargo,'vinculo',area=area,cargo=cargo)
        people = {}
        for alias, role in ROLES.items():
            email = f'demo.{alias}@saspel.com'
            user, fresh = m.Usuario.objects.get_or_create(pk=clave(m.Usuario,alias), defaults={
                'email':email, 'username':email, 'first_name':alias.capitalize(), 'last_name':'Demostración',
                'is_staff':alias=='sa', 'is_superuser':alias=='sa', 'debe_cambiar_password':alias=='nuevo'})
            if fresh:
                user.set_password(password)
                user.save(update_fields=['password'])
                user.groups.add(Group.objects.get_or_create(name=role)[0])
                m.PerfilUsuario.objects.create(usuario=user, codigo_empleado=f'H4-{alias.upper()}',
                   area=area,cargo=cargo,habilitado_asignaciones=alias=='psi',tamizaje_resuelto=alias=='trab')
            people[alias] = user
        policy = registro(m.PoliticaSistema,'privacidad',tipo='PRIVACIDAD_DATOS',titulo='Política de ensayo',
                          version='demo-1',contenido='Texto de demostración.',activo=True,obligatoria=True)
        for alias in ('sa','admin','trab','psi'):
            registro(m.AceptacionPolitica,alias,usuario=people[alias],politica=policy)
        worker, psy = people['trab'], people['psi']
        if people['nuevo'].groups.filter(name='NUEVO_TRABAJADOR').exists():
            AsignarEvaluacionInicial(DjangoAdministrationRepository()).execute(people['nuevo'].pk,'NUEVO_TRABAJADOR')
        registro(m.AsignacionProfesional,'asignacion',trabajador=worker,psicologo=psy)
        instrument = registro(m.InstrumentoPsicologico,'escala',codigo='H4-DEMO',nombre='Frecuencia de pausas (demo)')
        scale = registro(m.EscalaRespuesta,'escala',nombre='Frecuencia (demo)')
        options = [registro(m.OpcionRespuesta,n,escala=scale,etiqueta=label,valor=n,orden=n+1)
                   for n,label in enumerate(['Nunca','A veces','Siempre'])]
        question = registro(m.PreguntaInstrumento,'pausas',instrumento=instrument,escala=scale,
                           texto='¿Con qué frecuencia pospusiste una pausa esta semana?',orden=1,tipo_respuesta='ESCALA')
        band = registro(m.RangoInterpretacion,'banda',instrumento=instrument,nombre='Banda demo',
                       puntaje_minimo=0,puntaje_maximo=2,orden=1)
        registro(m.ReglaAlerta,'regla',nombre='Revisión de demostración',rango=band,nivel='MEDIA')
        now = timezone.now().astimezone(ZoneInfo('America/La_Paz'))
        for n in (1,2):
            when = now-timedelta(days=6-2*n)
            assignment = registro(m.AsignacionInstrumento,n,trabajador=worker,instrumento=instrument,
                                  asignado_por=psy,origen='PROFESIONAL',estado='COMPLETADA')
            app = registro(m.AplicacionInstrumento,n,asignacion=assignment,estado='FINALIZADA',
                           fecha_inicio=when-timedelta(minutes=3),fecha_finalizacion=when)
            registro(m.RespuestaPregunta,n,aplicacion=app,pregunta=question,opcion=options[n])
            registro(m.ResultadoInstrumento,n,aplicacion=app,rango=band,puntaje_total=n,fecha_calculo=when)
        start = (now+timedelta(days=2)).replace(hour=10,minute=0,second=0,microsecond=0)
        registro(m.DisponibilidadPsicologo,'agenda',psicologo=psy,dia_semana=start.weekday(),hora_inicio=time(8),hora_fin=time(17))
        registro(m.Cita,'cita',trabajador=worker,psicologo=psy,solicitada_por=worker,
                 fecha_inicio=start,fecha_fin=start+timedelta(minutes=30),motivo='Consulta de demostración')
        seguimiento = registro(m.Seguimiento,'plan',trabajador=worker,profesional=psy,motivo='Consulta demo',
            categoria='Orientación',observacion='Nota profesional de ensayo',estado='Abierto',
            evolucion='Revisión de pausas',plan_accion='Registrar una pausa')
        registro(m.Recomendacion,'accion',seguimiento=seguimiento,profesional=psy,
                 texto='Registrar una pausa durante la jornada de demostración.',compartida=True)
        self.stdout.write('Dataset H4 preparado. Los nuevos accesos usan la clave indicada por el operador.')

