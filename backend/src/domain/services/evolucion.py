from collections import OrderedDict
from decimal import Decimal


def agrupar_evolucion(resultados):
    """Compara únicamente puntajes de la misma versión; nunca infiere diagnósticos."""
    grupos = OrderedDict()
    for punto in resultados:
        key = punto['instrumento_id']
        grupo = grupos.setdefault(key, {k: punto[k] for k in ('instrumento_id', 'nombre', 'version')}
                                  | {'puntos': []})
        grupo['puntos'].append({k: punto[k] for k in ('resultado_id', 'fecha', 'puntaje', 'nivel')})
    for grupo in grupos.values():
        puntos = grupo['puntos']
        delta = Decimal(puntos[-1]['puntaje']) - Decimal(puntos[0]['puntaje']) if len(puntos) > 1 else None
        grupo['diferencia'] = str(delta) if delta is not None else None
        grupo['tendencia'] = ('SIN_COMPARACION' if delta is None else
                             'AUMENTO' if delta > 0 else 'DISMINUCION' if delta < 0 else 'SIN_CAMBIO')
    return list(grupos.values())
