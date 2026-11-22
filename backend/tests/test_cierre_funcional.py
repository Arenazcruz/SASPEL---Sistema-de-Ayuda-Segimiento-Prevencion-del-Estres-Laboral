"""Escenarios sintéticos H4: permisos, resolución posterior al onboarding y evolución."""
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from tests.test_citas_api import person
from src.infrastructure.persistence.django.models import (
    AsignacionProfesional, InstrumentoPsicologico, EscalaRespuesta, OpcionRespuesta,
    PreguntaInstrumento, RangoInterpretacion, AsignacionInstrumento, AplicacionInstrumento,
    ResultadoInstrumento, Seguimiento, Recomendacion, Notificacion,
)


class CierreFuncionalTests(TestCase):
    def setUp(self):
        self.w=person('h4worker','TRABAJADOR'); self.p=person('h4psy','PSICOLOGO')
        self.other=person('h4other','TRABAJADOR'); self.foreign=person('h4foreign','PSICOLOGO')
        self.admin=person('h4admin','SUPERADMIN'); self.new=person('h4new','NUEVO_TRABAJADOR')
        self.link=AsignacionProfesional.objects.create(trabajador=self.w,psicologo=self.p)
        self.instrument=InstrumentoPsicologico.objects.create(codigo='H4-SINTETICO',nombre='Escala sintética')
        self.scale=EscalaRespuesta.objects.create(nombre='Opciones sintéticas')
        self.option=OpcionRespuesta.objects.create(escala=self.scale,etiqueta='Prueba',valor=2,orden=1)
        self.question=PreguntaInstrumento.objects.create(instrumento=self.instrument,escala=self.scale,texto='Pregunta sintética',orden=1,tipo_respuesta='ESCALA')
        RangoInterpretacion.objects.create(instrumento=self.instrument,nombre='Banda sintética',puntaje_minimo=0,puntaje_maximo=10,orden=1)
        self.client=APIClient()
        self.url=f'/api/psicologo/trabajadores/{self.w.pk}/instrumentos/'
        self.seg=Seguimiento.objects.create(trabajador=self.w,profesional=self.p,motivo='Sintético',categoria='Prueba',observacion='Privado',estado='Seguimiento',evolucion='Prueba',plan_accion='Prueba')
        self.rec=f'/api/seguimientos/{self.seg.pk}/recomendaciones/'

    def auth(self,user):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+str(AccessToken.for_user(user)))

    def asignar(self):
        self.auth(self.p)
        response=self.client.post(self.url,{'instrumento_id':str(self.instrument.pk)},format='json')
        self.assertEqual(response.status_code,201,response.data)
        return str(response.data['id'])

    def test_asignar_resolver_y_repetir_sin_rehacer_onboarding(self):
        pk=self.asignar(); self.auth(self.w); url=f'/api/trabajador/evaluaciones/{pk}/'
        self.assertEqual(len(self.client.get('/api/trabajador/instrumentos/').data['asignaciones']),1)
        self.assertEqual(self.client.post(url+'iniciar/',{},format='json').status_code,200)
        data={'respuestas':[{'pregunta_id':str(self.question.pk),'opcion_id':str(self.option.pk)}]}
        result=self.client.post(url+'finalizar/',data,format='json')
        self.assertEqual(result.status_code,200,result.data)
        self.assertEqual(result.data['puntaje_total'],'2.0000')
        self.assertEqual(self.client.post(url+'finalizar/',data,format='json').status_code,200)
        self.assertEqual(self.client.post(url+'respuestas/',data,format='json').status_code,400)
        self.assertEqual(ResultadoInstrumento.objects.count(),1)
        self.assertEqual(AsignacionProfesional.objects.count(),1)
        self.assertFalse(self.w.perfil_usuario.tamizaje_resuelto)  # no transición de onboarding
        self.asignar()  # otra aplicación independiente después del cierre

    def test_duplicado_y_plazo_pasado(self):
        self.asignar();self.auth(self.p)
        self.assertEqual(self.client.post(self.url,{'instrumento_id':str(self.instrument.pk)},format='json').status_code,400)
        self.assertEqual(self.client.post(self.url,{'instrumento_id':str(self.instrument.pk),'fecha_limite':(timezone.now()-timedelta(days=1)).isoformat()},format='json').status_code,400)
        self.assertEqual(AsignacionInstrumento.objects.count(),1)

    def test_asignacion_no_admite_inactivos_sin_preguntas_ni_inicial(self):
        self.auth(self.p)
        for changes in ({'activo':False},{'activo':True,'es_inicial':True}):
            InstrumentoPsicologico.objects.filter(pk=self.instrument.pk).update(**changes)
            self.assertEqual(self.client.post(self.url,{'instrumento_id':str(self.instrument.pk)},format='json').status_code,400)
        InstrumentoPsicologico.objects.filter(pk=self.instrument.pk).update(es_inicial=False)
        self.question.activo=False;self.question.save()
        self.assertEqual(self.client.post(self.url,{'instrumento_id':str(self.instrument.pk)},format='json').status_code,400)

    def test_permisos_asignacion_y_resolucion(self):
        for actor,status in ((self.w,403),(self.new,403),(self.foreign,404)):
            self.auth(actor);self.assertEqual(self.client.get(self.url).status_code,status)
        pk=self.asignar()
        for actor,status in ((self.other,404),(self.p,403),(self.admin,403),(self.new,403)):
            self.auth(actor);self.assertEqual(self.client.get(f'/api/trabajador/evaluaciones/{pk}/').status_code,status)
        self.link.estado='FINALIZADA';self.link.save();self.auth(self.p)
        self.assertEqual(self.client.get(self.url).status_code,404)

    def test_nuevo_no_resuelve_instrumento_profesional_por_ruta_inicial(self):
        pk=self.asignar();self.auth(self.new)
        AsignacionInstrumento.objects.filter(pk=pk).update(trabajador=self.new)
        self.assertEqual(self.client.get(f'/api/nuevo-trabajador/evaluaciones/{pk}/').status_code,404)

    def test_notificacion_dirigida_sin_contenido_clinico(self):
        pk=self.asignar()
        self.assertTrue(Notificacion.objects.filter(destinatario=self.w,origen_id=pk,tipo='INSTRUMENTO').exists())
        self.assertFalse(Notificacion.objects.filter(destinatario=self.other,origen_id=pk).exists())

    def test_version_usada_conserva_preguntas_escalas_y_metadatos(self):
        pk=self.asignar();self.auth(self.w)
        self.client.post(f'/api/trabajador/evaluaciones/{pk}/iniciar/',{},format='json')
        from src.infrastructure.persistence.django.repositories.instrument_content import DjangoContentRepository
        from src.infrastructure.persistence.django.repositories.instruments import DjangoInstrumentRepository
        from src.domain.exceptions.superadmin import AdministrationError
        repo=DjangoContentRepository()
        for kind,parent,item,changes in [('questions',self.instrument.pk,self.question.pk,{'texto':'Cambio'}),('options',self.scale.pk,self.option.pk,{'valor':9})]:
            with self.assertRaises(AdministrationError),repo.atomic(kind,parent):
                repo.update(kind,parent,item,changes)
        with self.assertRaises(AdministrationError):
            DjangoInstrumentRepository().update(self.instrument.pk,{'version':'Sobrescrita'})
        DjangoInstrumentRepository().set_active(self.instrument.pk,False)
        self.question.refresh_from_db();self.assertEqual(self.question.texto,'Pregunta sintética')

    def test_recomendaciones_transiciones_autoria_y_privacidad(self):
        self.auth(self.p)
        response=self.client.post(self.rec,{'texto':'Recomendación sintética'},format='json')
        self.assertEqual(response.status_code,201,response.data); pk=response.data['id']
        url=f'{self.rec}{pk}/estado/'
        for estado in ['EN_PROGRESO','COMPLETADA']:
            self.assertEqual(self.client.post(url,{'estado':estado},format='json').status_code,200)
        self.assertEqual(self.client.post(url,{'estado':'EN_PROGRESO'},format='json').status_code,400)
        self.assertEqual(Recomendacion.objects.get(pk=pk).profesional,self.p)
        for actor,status in ((self.w,403),(self.admin,403),(self.foreign,404)):
            self.auth(actor); self.assertEqual(self.client.get(self.rec).status_code,status)
        self.link.estado='FINALIZADA';self.link.save();self.auth(self.p)
        self.assertEqual(self.client.get(self.rec).status_code,404)

    def test_recomendacion_no_falsifica_autor_y_no_admite_vacio(self):
        self.auth(self.p)
        for data in ({'texto':' '},{'texto':'Texto','profesional_id':str(self.foreign.pk)}):
            self.assertEqual(self.client.post(self.rec,data,format='json').status_code,400)
        self.assertEqual(Recomendacion.objects.count(),0)

    def resultado(self,instrumento,score,days):
        a=AsignacionInstrumento.objects.create(trabajador=self.w,instrumento=instrumento,origen='PROFESIONAL',estado='COMPLETADA')
        app=AplicacionInstrumento.objects.create(asignacion=a,estado='FINALIZADA',fecha_finalizacion=timezone.now()+timedelta(days=days))
        return ResultadoInstrumento.objects.create(aplicacion=app,puntaje_total=score,fecha_calculo=timezone.now())

    def test_evolucion_separa_versiones_y_excluye_invalidos(self):
        self.resultado(self.instrument,2,-2);self.resultado(self.instrument,4,-1)
        otra=InstrumentoPsicologico.objects.create(codigo=self.instrument.codigo,version='2',nombre='Otra versión')
        self.resultado(otra,100,0)
        invalid=self.resultado(self.instrument,999,1);invalid.deleted=True;invalid.save()
        self.auth(self.w); r=self.client.get('/api/trabajador/evolucion/')
        self.assertEqual(r.status_code,200,r.data)
        self.assertEqual(len(r.data['series']),2)
        serie=r.data['series'][0]
        self.assertEqual(serie['tendencia'],'AUMENTO');self.assertEqual(serie['diferencia'],'2.0000')
        self.assertEqual(len(serie['puntos']),2)
        self.assertEqual(r.data['series'][1]['tendencia'],'SIN_COMPARACION')
        self.assertEqual(r['Cache-Control'],'no-store')

    def test_evolucion_filtros_permisos_y_vacio(self):
        self.auth(self.other);self.assertEqual(self.client.get('/api/trabajador/evolucion/').data,{'series':[]})
        self.assertEqual(self.client.get('/api/trabajador/evolucion/?desde=2026-02-01&hasta=2026-01-01').status_code,400)
        self.assertEqual(self.client.get('/api/trabajador/evolucion/?desde=invalida').status_code,400)
        url=f'/api/psicologo/trabajadores/{self.w.pk}/evolucion/'
        for actor,status in ((self.p,200),(self.foreign,404),(self.admin,403),(self.w,403)):
            self.auth(actor);self.assertEqual(self.client.get(url).status_code,status)
