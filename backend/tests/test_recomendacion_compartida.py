from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from src.infrastructure.persistence.django.models import AsignacionProfesional, Seguimiento
from tests.test_citas_api import person


class CompartirTests(TestCase):
    def test_publicar_solo_texto_expresamente_compartido(self):
        worker = person('receptor', 'TRABAJADOR')
        psy = person('autor', 'PSICOLOGO')
        other = person('vecino', 'TRABAJADOR')
        AsignacionProfesional.objects.create(trabajador=worker, psicologo=psy)
        seg = Seguimiento.objects.create(trabajador=worker, profesional=psy, observacion='Nota privada')
        api = APIClient()
        def entrar(user):
            api.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(user)))
        entrar(psy)
        url = f'/api/seguimientos/{seg.pk}/recomendaciones/'
        for body in [{'texto':'Solo profesional'}, {'texto':'Acción compartida','compartida':True}]:
            self.assertEqual(api.post(url,body,format='json').status_code,201)
        propias='/api/trabajador/recomendaciones/'
        self.assertEqual(api.get(propias).status_code,403)
        entrar(worker)
        row, = api.get(propias).data
        self.assertEqual(set(row), {'id','texto','estado','creado_en'})
        self.assertEqual(row['texto'],'Acción compartida')
        from src.infrastructure.persistence.django.repositories.notificaciones import DjangoNotificacionesRepository
        from src.infrastructure.persistence.django.models import Recomendacion
        visible = Recomendacion.objects.get(compartida=True)
        visible.save()
        avisos = DjangoNotificacionesRepository().visibles(worker.pk).filter(tipo='RECOMENDACION')
        self.assertEqual(avisos.count(), 1)
        self.assertEqual(avisos.get().origen_id, visible.pk)
        self.assertNotIn(visible.texto, avisos.get().titulo)
        entrar(other)
        self.assertEqual(api.get(propias,{'trabajador_id':worker.pk}).data,[])
