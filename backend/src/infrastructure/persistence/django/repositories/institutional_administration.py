from src.domain.services.institutional_administration import PERSONNEL_ROLES, validate_institutional_creation
from src.domain.exceptions.superadmin import AdministrationError
from .administration import DjangoAdministrationRepository


class DjangoInstitutionalAdministrationRepository(DjangoAdministrationRepository):
    """El mismo CRUD probado con un conjunto de cuentas estrictamente más reducido."""
    @staticmethod
    def users():
        return DjangoAdministrationRepository.users().filter(functional_role__in=PERSONNEL_ROLES)

    def create_user(self, command):
        validate_institutional_creation(command.role)
        return super().create_user(command)

    def set_role(self, user_id, role):
        raise AdministrationError('Los cambios de rol corresponden a Superadmin.')
