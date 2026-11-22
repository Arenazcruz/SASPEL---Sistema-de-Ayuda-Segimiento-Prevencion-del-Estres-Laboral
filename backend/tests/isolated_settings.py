"""Configuración cerrada: solo el clúster temporal creado por run_isolated.py."""
import os
from pathlib import Path

if (os.getenv('SASPEL_ISOLATED') != '1'
        or os.getenv('PYTHON_DOTENV_DISABLED') != '1'
        or os.getenv('POSTGRES_DB') != 'saspel_verificacion'
        or os.getenv('POSTGRES_HOST') != '127.0.0.1'
        or not Path(os.getenv('SASPEL_TEMP_CLUSTER', ''), 'PG_VERSION').is_file()):
    raise RuntimeError('Ejecutar mediante tests/run_isolated.py; no usar una BD real.')

from config.settings import *  # noqa: E402,F403

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
DATABASES['default']['TEST'] = {'NAME': 'test_saspel_verificacion'}  # noqa: F405
CACHES = {alias: {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                  'LOCATION': 'verificacion-' + alias}
          for alias in ('default', 'login_attempts')}
