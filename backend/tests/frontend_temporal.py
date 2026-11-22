"""Sirve la compilación local de Angular durante una prueba de navegador."""
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlsplit


@contextmanager
def frontend_temporal(root, env):
    if env.get('SASPEL_FRONTEND_URL'):
        yield
        return
    directory = root / 'frontend/dist/frontend/browser'
    if not (directory / 'index.html').is_file():
        raise RuntimeError('Ejecuta npm run build en frontend antes del ensayo.')
    class Angular(SimpleHTTPRequestHandler):
        def do_GET(self):
            if not Path(urlsplit(self.path).path).suffix:
                self.path = '/index.html'
            super().do_GET()

        def log_message(self, *args):
            pass
    with ThreadingHTTPServer(('127.0.0.1',0),partial(Angular,directory=str(directory))) as server:
        thread=Thread(target=server.serve_forever,daemon=True)
        thread.start()
        env['SASPEL_FRONTEND_URL']=f'http://127.0.0.1:{server.server_port}'
        try:
            yield
        finally:
            server.shutdown()
            thread.join()
