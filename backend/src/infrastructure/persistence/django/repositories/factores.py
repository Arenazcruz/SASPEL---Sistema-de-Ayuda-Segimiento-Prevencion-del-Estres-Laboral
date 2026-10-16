from django.db.models import Q
from src.infrastructure.persistence.django.models import FactorPsicosocial, TipoFactorPsicosocial
from src.infrastructure.persistence.django.repositories.resultados import DjangoResultadosRepository
from src.domain.exceptions.resultados import ResultadoNoDisponible
from src.domain.exceptions.superadmin import AdministrationError

class DjangoFactoresRepository(DjangoResultadosRepository):
    def rol_catalogo(self, actor):
        # La cuenta administrativa de bootstrap no necesita un perfil de trabajador.
        return self.administration.users().filter(pk=actor,is_active=True,deleted=False).filter(
            Q(perfil_usuario__isnull=True)|Q(perfil_usuario__deleted=False)
        ).values_list('functional_role',flat=True).first()

    @staticmethod
    def dto(row):
        return {'id':row.pk,'tipo_id':row.tipo_id,'tipo':row.tipo_nombre,'nivel':row.nivel,'descripcion':row.descripcion,'fecha':row.creado_en}

    @staticmethod
    def tipo_dto(row):
        return {'id':row.pk,'nombre':row.nombre,'descripcion':row.descripcion,'activo':row.activo}

    def historial(self, trabajador):
        user = self.usuarios().get(pk=trabajador)
        rows = FactorPsicosocial.objects.filter(trabajador_id=trabajador,deleted=False)
        return {'trabajador':user.get_full_name() or user.email,'registros':[self.dto(row) for row in rows]}

    def registrar(self, trabajador, datos):
        tipo = TipoFactorPsicosocial.objects.filter(pk=datos.tipo_id,activo=True,deleted=False).first()
        if not tipo:
            raise AdministrationError('El tipo de factor ya no está disponible. Actualiza el catálogo.')
        row = FactorPsicosocial.objects.create(trabajador_id=trabajador,tipo=tipo,tipo_nombre=tipo.nombre,
                nivel=datos.nivel,descripcion=datos.descripcion,creado_por=str(trabajador),actualizado_por=str(trabajador))
        return self.dto(row)

    def catalogo(self, incluir_inactivos):
        rows = TipoFactorPsicosocial.objects.filter(deleted=False)
        if not incluir_inactivos:
            rows = rows.filter(activo=True)
        return [self.tipo_dto(row) for row in rows]

    def guardar_tipo(self, actor, datos, tipo_id=None):
        nombre = datos['nombre'].strip()
        if not nombre or len(nombre)>120 or len(datos.get('descripcion',''))>1000:
            raise AdministrationError('Nombre o descripción de tipo no válido.')
        if TipoFactorPsicosocial.objects.filter(nombre__iexact=nombre).exclude(pk=tipo_id).exists():
            raise AdministrationError('Ya existe un tipo con ese nombre.')
        row = TipoFactorPsicosocial.objects.filter(pk=tipo_id,deleted=False).first() if tipo_id else TipoFactorPsicosocial(creado_por=str(actor))
        if row is None:
            raise ResultadoNoDisponible('El tipo no está disponible.')
        row.nombre=nombre;row.descripcion=datos.get('descripcion','');row.activo=datos['activo'];row.actualizado_por=str(actor)
        row.full_clean();row.save()
        return self.tipo_dto(row)
