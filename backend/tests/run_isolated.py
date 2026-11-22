"""Pruebas reproducibles sobre PostgreSQL temporal, con opción --browser.

Requiere psycopg y binarios initdb/pg_ctl en SASPEL_TEST_PG_BIN.
No lee .env, no usa la BD de desarrollo y elimina solo su TemporaryDirectory.
Ejemplo: python backend/tests/run_isolated.py tests
"""
import argparse
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', action='store_true')
    parser.add_argument('--schema', action='store_true', help='Verificar migración, reversión y respaldo/restauración sintéticos.')
    parser.add_argument('labels', nargs='*', default=['tests'])
    args = parser.parse_args()
    backend = Path(__file__).resolve().parents[1]
    binaries = Path(os.getenv('SASPEL_TEST_PG_BIN', r'C:\Program Files\PostgreSQL\18\bin'))
    suffix = '.exe' if os.name == 'nt' else ''
    commands = {name: str(binaries / (name + suffix)) if (binaries / (name + suffix)).is_file()
                else shutil.which(name) for name in ('initdb', 'pg_ctl', 'pg_dump', 'pg_restore')}
    if not all(commands.values()):
        parser.error('Faltan binarios PostgreSQL. No se intentará usar la base habitual.')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(('PG', 'POSTGRES_', 'DJANGO_', 'SASPEL_LOGIN_'))}
    password = secrets.token_urlsafe(36)
    with tempfile.TemporaryDirectory(prefix='saspel-verificacion-') as temporary:
        root = Path(temporary)
        cluster = root / 'cluster'
        pwfile = root / 'password'
        pwfile.write_text(password, encoding='utf-8')
        env.update(PYTHON_DOTENV_DISABLED='1', SASPEL_ISOLATED='1',
                   SASPEL_TEMP_CLUSTER=str(cluster), DJANGO_SETTINGS_MODULE='tests.isolated_settings',
                   DJANGO_SECRET_KEY=secrets.token_urlsafe(64), DJANGO_DEBUG='False',
                   POSTGRES_DB='saspel_verificacion', POSTGRES_USER='verificador',
                   POSTGRES_PASSWORD=password, POSTGRES_HOST='127.0.0.1', POSTGRES_PORT=str(port),
                   PYTHONIOENCODING='utf-8', SASPEL_BROWSER_TEST='1' if args.browser else '0')

        def pg(name, *arguments):
            # Archivos evitan que el servidor herede pipes abiertos en Windows.
            with (root / 'commands.log').open('a', encoding='utf-8') as log:
                subprocess.run([commands[name], *map(str, arguments)], env=env, check=True,
                               stdout=log, stderr=log, timeout=60)

        def manage(*arguments):
            subprocess.run([sys.executable, 'manage.py', *arguments], cwd=backend, env=env, check=True)

        pg('initdb', '-D', cluster, '-U', 'verificador', '-A', 'scram-sha-256',
           '--pwfile', pwfile, '--encoding=UTF8', '--locale=C')
        pwfile.unlink()
        try:
            pg('pg_ctl', '-D', cluster, '-l', root / 'postgres.log', '-w', '-o', f'-p {port} -h 127.0.0.1', 'start')
            import psycopg
            with psycopg.connect(host='127.0.0.1', port=port, user='verificador',
                                 password=password, dbname='postgres', autocommit=True) as conn:
                actual = conn.execute('SHOW data_directory').fetchone()[0]
                if Path(actual).resolve() != cluster.resolve():
                    raise RuntimeError('No coincide el directorio del servidor temporal.')
                conn.execute('CREATE DATABASE saspel_verificacion')
                if args.schema:
                    conn.execute('CREATE DATABASE saspel_restauracion')
            print('PostgreSQL temporal verificado; .env deshabilitado; datos sintéticos.', flush=True)
            if args.schema:
                manage('migrate', '--noinput')
                manage('check')
                manage('makemigrations', '--check', '--dry-run')
                # Reversión solo en el clúster recién creado, nunca en desarrollo.
                manage('migrate', 'api', '0012', '--noinput')
                manage('migrate', '--noinput')
                manage('shell', '--command',
                       "from src.infrastructure.persistence.django.models import AreaInstitucional,CargoInstitucional,AreaCargo; "
                       "a=AreaInstitucional.objects.create(nombre='Respaldo sintético'); "
                       "c=CargoInstitucional.objects.create(nombre='Cargo sintético de respaldo'); "
                       "AreaCargo.objects.create(area=a,cargo=c)")
                env['PGPASSWORD'] = password
                connection = ['-h', '127.0.0.1', '-p', str(port), '-U', 'verificador']
                pg('pg_dump', *connection, '-Fc', '-f', root / 'synthetic.dump', 'saspel_verificacion')
                pg('pg_restore', *connection, '--exit-on-error', '-d', 'saspel_restauracion', root / 'synthetic.dump')
                with psycopg.connect(host='127.0.0.1', port=port, user='verificador', password=password,
                                     dbname='saspel_restauracion') as restored:
                    count = restored.execute('SELECT COUNT(*) FROM django_migrations').fetchone()[0]
                    if count < 15:
                        raise RuntimeError('Restauración sin historial de migraciones completo.')
                    restored_link = restored.execute(
                        "SELECT COUNT(*) FROM saspel_area_cargo ac "
                        "JOIN saspel_area_institucional a ON ac.area_id=a.id "
                        "JOIN saspel_cargo_institucional c ON ac.cargo_id=c.id "
                        "WHERE a.nombre=%s AND c.nombre=%s",
                        ('Respaldo sintético', 'Cargo sintético de respaldo'),
                    ).fetchone()[0]
                    if restored_link != 1:
                        raise RuntimeError('No se recuperó el vínculo sintético del respaldo.')
                print('Migración, reversión 0015→0012→0015 y pg_dump/pg_restore comprobados.', flush=True)
            else:
                manage('test', *(args.labels or ['tests']), '--noinput', '--verbosity=2')
            return 0
        finally:
            if (cluster / 'postmaster.pid').exists():
                pg('pg_ctl', '-D', cluster, '-m', 'fast', '-w', 'stop')
            print('Clúster temporal detenido; limpieza limitada a su directorio.', flush=True)


if __name__ == '__main__':
    raise SystemExit(main())
