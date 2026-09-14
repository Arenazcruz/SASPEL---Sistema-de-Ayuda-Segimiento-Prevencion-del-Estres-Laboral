"""Este archivo reúne los modelos que Django debe reconocer al iniciar SASPEL.

Cada modelo se mantiene en su propio archivo para encontrarlo fácilmente.
Importarlos aquí permite que Django los descubra; no crea registros de ejemplo.
"""

from .aplicacion_instrumento import AplicacionInstrumento
from .area_institucional import AreaInstitucional
from .asignacion_instrumento import AsignacionInstrumento
from .asignacion_profesional import AsignacionProfesional
from .cargo_institucional import CargoInstitucional
from .cita import Cita
from .disponibilidad_psicologo import DisponibilidadPsicologo
from .escala_respuesta import EscalaRespuesta
from .instrumento_psicologico import InstrumentoPsicologico
from .opcion_respuesta import OpcionRespuesta
from .perfil_usuario import PerfilUsuario
from .pregunta_instrumento import PreguntaInstrumento
from .rango_interpretacion import RangoInterpretacion
from .respuesta_pregunta import RespuestaPregunta
from .resultado_instrumento import ResultadoInstrumento

__all__ = [
    'AplicacionInstrumento',
    'AreaInstitucional',
    'AsignacionInstrumento',
    'AsignacionProfesional',
    'CargoInstitucional',
    'Cita',
    'DisponibilidadPsicologo',
    'EscalaRespuesta',
    'InstrumentoPsicologico',
    'OpcionRespuesta',
    'PerfilUsuario',
    'PreguntaInstrumento',
    'RangoInterpretacion',
    'RespuestaPregunta',
    'ResultadoInstrumento',
]
