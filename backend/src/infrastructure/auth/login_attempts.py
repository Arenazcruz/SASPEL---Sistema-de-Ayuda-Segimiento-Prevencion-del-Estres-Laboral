"""Presupuesto temporal de fallos de login; no modifica cuentas ni sesiones."""

from math import ceil
from time import time

from django.core.cache import caches
from django.utils.crypto import salted_hmac


class LoginAttemptBudget:
    WINDOW_SECONDS = 300
    EMAIL_LIMIT = 5
    IP_LIMIT = 20

    def __init__(self, email: str, ip: str):
        self.cache = caches['login_attempts']
        now = time()
        self.window = int(now // self.WINDOW_SECONDS)
        self.wait = max(1, ceil((self.window + 1) * self.WINDOW_SECONDS - now))
        self.scopes = (('ip', ip, self.IP_LIMIT), ('email', email.strip().lower(), self.EMAIL_LIMIT))
        self.reserved = []

    def reserve(self) -> bool:
        """Reserva antes del hash para incluir solicitudes simultáneas en el límite.

        Cada ventana tiene claves propias: una respuesta tardía nunca decrementa
        el contador de la siguiente ventana. El TTL no se renueva al incrementar.
        """
        for scope, value, limit in self.scopes:
            digest = salted_hmac('saspel.login.' + scope, value, algorithm='sha256').hexdigest()
            key = f'login-failures:{self.window}:{scope}:{digest}'
            self.cache.add(key, 0, timeout=self.wait + 1)
            try:
                count = self.cache.incr(key)
            except ValueError:
                # La clave pudo caducar entre add e incr; no admitir sin reserva.
                self.release()
                return False
            self.reserved.append(key)
            if count > limit:
                self.release()
                return False
        return True

    def release(self):
        """Libera solo este intento si tuvo éxito o no llegó a autenticarse."""
        for key in self.reserved:
            try:
                self.cache.decr(key)
            except ValueError:
                pass  # Una reserva de una ventana expirada ya no necesita limpieza.
        self.reserved.clear()
