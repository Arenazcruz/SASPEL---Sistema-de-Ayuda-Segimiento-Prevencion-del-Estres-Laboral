"""Conserva la respuesta histórica de /api/ para comprobar conexión con Django. No consulta casos
de uso ni base de datos; test_health_api.py protege ese contrato.
"""

from django.http import JsonResponse


def prueba(request):
    """Conserva la respuesta de prueba existente en /api/."""
    return JsonResponse({
        'mensaje': 'Django funciona',
    })
