"""Guardas de imports estáticos; no requieren instalar ni iniciar Django."""

import ast
from importlib.util import resolve_name
from pathlib import Path
import sys
from unittest import TestCase


BACKEND_DIR = Path(__file__).resolve().parent.parent
# Transporte y almacenamiento corresponden a Infrastructure, incluso si son de stdlib.
EXTERNAL_DETAILS = {'http', 'urllib', 'socket', 'sqlite3'}


class ArchitectureTests(TestCase):
    """Protege los imports permitidos de Domain y Application sin cargar frameworks."""
    def assert_layer_imports(self, layer, allowed_layers):
        """Recorre Python de la capa recibida y falla si encuentra imports fuera de
        allowed_layers o biblioteca estándar permitida. EXTERNAL_DETAILS excluye
        transporte/almacenamiento incluso si pertenecen a stdlib.
        """
        files = sorted((BACKEND_DIR / 'src' / layer).rglob('*.py'))
        self.assertTrue(files, f'Missing layer: {layer}')
        for path in files:
            package = '.'.join(path.parent.relative_to(BACKEND_DIR).parts)
            tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    if node.level:
                        module = resolve_name('.' * node.level + module, package)
                    imports = [f'{module}.{alias.name}' for alias in node.names]
                else:
                    continue

                for module in imports:
                    root = module.split('.')[0]
                    allowed = (
                        root in sys.stdlib_module_names
                        and root not in EXTERNAL_DETAILS
                    ) or any(
                        module == prefix or module.startswith(prefix + '.')
                        for prefix in allowed_layers
                    )
                    with self.subTest(file=str(path.relative_to(BACKEND_DIR)),
                                      line=node.lineno, imported=module):
                        self.assertTrue(allowed, f'Forbidden import: {module}')

    def test_domain_depends_only_on_itself_and_standard_library(self):
        """Revisa Domain para evitar que una regla dependa de Django, HTTP o Application."""
        self.assert_layer_imports('domain', ('src.domain',))

    def test_application_depends_only_on_core_and_standard_library(self):
        """Revisa Application para que los casos sigan dependiendo de contratos y dominio, sin
        Infrastructure.
        """
        self.assert_layer_imports('application', ('src.application', 'src.domain'))
