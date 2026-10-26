# Informe de implementación SASPEL — 26/10/2026

## 1. Resumen ejecutivo

Se auditó SASPE-UF como referencia estática y se completaron los flujos pendientes
verificables de SASPEL en la rama `codex/completar-saspel-referencia`. La solución
mantiene Django/Angular/PostgreSQL, sus reglas vigentes y una sola institución,
según confirmación del usuario. Hay **70/74 requisitos verificados (94,59 %)**;
no se declara cierre completo de las validaciones no funcionales ni aceptación
formal del hito. No hubo push, merge ni modificación del Excel/Word o de SASPE-UF.

## 2. Estado inicial encontrado

La base tenía onboarding, asignación profesional, instrumentos iniciales,
resultados, agenda, seguimiento, ánimo, factores, alertas, notificaciones y
reportes. Había 12 migraciones de aplicación y 28 modelos registrados. La línea
base dio 427 pruebas backend aprobadas y una omitida, y 209 frontend aprobadas.
Faltaban conexiones funcionales de H4, gestión efectiva de Admin y revocación
remota de sesiones. La presencia de archivos no se tomó como demostración de
funcionamiento. [Auditoría completa](AUDITORIA.md).

## 3. Funcionalidades aprovechadas de SASPE-UF

Referencia conceptual: asignar instrumentos y listar pendientes, resolver y
consultar resultados, agenda profesional, historial y perfil. Se tradujeron a
casos de uso y repositorios actuales. No se copiaron sintaxis, datos, tablas ni
umbrales clínicos. Se descartaron chat, diario, Markov y mecanismos inseguros de
contraseñas o difusión de datos. El esquema físico/ejecución de Laravel no se
verificó. [Equivalencias por requisito](MATRIZ.md).

## 4. Funcionalidades existentes conservadas

UUID y bajas lógicas; onboarding y aceptación; transición Nuevo Trabajador →
Trabajador; menor carga y desempate de psicólogos; restricciones de objeto;
puntuación configurada; citas y disponibilidad; notas privadas; seguimiento;
ánimo/factores; alertas explícitas; notificaciones dirigidas; reportes CSV seguros;
panel Superadmin y protección del último administrador. Se ejecutó regresión de
los módulos existentes y no se eliminaron controles para obtener pruebas verdes.

## 5. Funcionalidades nuevas implementadas

Reprogramación con cita sucesora e historial; asignación y resolución profesional
posterior al onboarding; recomendaciones manuales; evolución por instrumento y
versión; registro y consulta de auditoría; publicación/versionado de políticas;
perfil propio; cierre con revocación de sesiones; gestión Admin de personal,
instrumentos, catálogos y reasignaciones; vinculación de cargos por área.
Navegación, estados de carga/vacío/error y pruebas acompañan estos flujos.

## 6. Problemas corregidos

Tokens anteriores válidos después de cerrar o cambiar contraseña; falta de
gestión institucional para ADMIN; área/cargo creada sin poder vincularla desde
UI; reprogramación incompleta; falta de evaluación posterior al onboarding;
edición de contenido de versiones utilizadas; ausencia de auditoría consultable
y evolución comparable. Se probaron duplicados concurrentes y accesos por UUID
ajeno. No se introdujo acceso administrativo a notas clínicas.

## 7. Cambios arquitectónicos

Se añadieron puertos, casos, servicios de dominio y adaptadores ORM/API sin
dependencias Django/DRF en Domain/Application. Angular mantiene features y
ViewModels. Un contexto de administración reutiliza el CRUD probado con API y
permisos acotados. No se añadieron servicios externos ni dependencias de gráficos.
[Decisiones, rutas, permisos y límites](IMPLEMENTACION.md).

## 8. Migraciones realizadas

0013 Recomendacion, 0014 EventoAuditoria y 0015 Usuario.version_sesion. Son
aditivas; instalación/reversión/reaplicación se verificaron en PostgreSQL temporal.
En la base local se aplicaron después de generar y comprobar un respaldo privado;
los conteos de las 30 tablas SASPEL preexistentes se conservaron. No hay
migraciones pendientes ni diferencias de modelos. No se revirtió ninguna tabla
real. La restauración probada se hizo en otra base sintética.

## 9. Resultados de pruebas

- Backend del workspace: **462 aprobadas**, 2 omitidas por ser de navegador,
  0 fallos; incluye 24 pruebas SQL ajenas preexistentes conservadas.
- Backend exclusivamente versionado: **438 aprobadas**, las mismas 2 omitidas,
  0 fallos; reproducible sin archivos locales ajenos.
- Navegador separado: **2 aprobadas**, 0 omitidas/fallidas, Angular/API real y
  datos sintéticos. Incluye móvil, Admin y permisos negativos.
- Frontend: **222 aprobadas en 23 archivos**, 0 fallidas. Build de producción
  correcto. Django check y pip check correctos.
- Migraciones, restricciones y respaldo/restauración sintética correctos.

No se cuentan repeticiones selectivas como casos nuevos. [Resultados, fallos de
iteración resueltos y límites](PRUEBAS.md), [evidencia](evidencias/resumen.json).

## 10. Archivos modificados

El listado completo por estado Git está en [ARCHIVOS.md](ARCHIVOS.md), con rutas
del backend, frontend, pruebas y documentación. No incluye archivos ajenos de
`gestion/`, `docs/seguridad/` ni los cuatro archivos locales de auditoría SQL.
El [inventario estático](inventario.json) identifica 194 archivos de referencia y
496 fuentes SASPEL examinadas por el inventariador; no equivale a cobertura de
líneas ni a ejecución de todos los archivos de Laravel.

## 11. Commits generados

Base: `4acb223`. Rama de trabajo: `codex/completar-saspel-referencia`.

| Commit | Cambio |
| --- | --- |
| `5bf5452` | Plan y límites de adaptación. |
| `c4a8307` | Reprogramación transaccional e historial. |
| `044ad68` | Recomendaciones profesionales privadas. |
| `d793cc5` | Políticas y auditoría de metadatos. |
| `8296304` | Revocación de sesiones y perfil propio. |
| `8ac36d9` | Asignar/resolver instrumentos de seguimiento. |
| `f84cf70` | Evolución comparable por versión. |
| `8f85762` | Personal y catálogos de la institución única. |
| `74b8900` | Integración H4, PostgreSQL aislado y navegador. |

El commit documental que contiene este informe tiene el asunto
`docs: cerrar auditoría, trazabilidad y evidencia de SASPEL`; su identificador
se obtiene con `git log -1 --format=oneline -- docs/completar/INFORME.md`.
No se publicó ni integró ninguna rama remota.

## 12. Pendientes y bloqueos

RNF-18: evaluación integral de usabilidad con usuarios; RNF-19: tablets y motores
adicionales a Edge; RNF-20: carga representativa y umbral aceptable acordado;
RNF-24: validación mediante extensión futura real. T67/T68: ensayo aprobado y
presentación/aceptación formal. Son pendientes de validación o aceptación, no
funciones silenciosamente declaradas completas.

La auditoría cubre mutaciones exitosas, no todas las lecturas, ni es inviolable
ante SQL administrativo directo. Logout sin conectividad no garantiza revocación
remota. No se ejecutó Laravel, no se migraron datos clínicos, no se certificaron
textos legales ni se desplegó a producción. Los bloqueos compartidos requieren
medición de carga. No quedan fallos críticos conocidos en los escenarios probados;
esto no constituye una garantía universal de seguridad o disponibilidad.

## 13. Instrucciones de ejecución

Con `.env` y PostgreSQL locales configurados: ejecutar
`.\.venv\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8000` y,
desde `frontend`, `npm.cmd start`; abrir `http://localhost:4200`.
Las migraciones ya están aplicadas en esta máquina. Para otro entorno, instalar
dependencias fijadas, respaldar y aplicar `migrate` antes de arrancar.
[GUIA.md](GUIA.md) detalla instalación, roles, demo, pruebas aisladas, navegador
y recuperación sin sobrescribir la base habitual.

## 14. Porcentaje y método de cobertura

Denominador: **49 RF vigentes + 25 RNF = 74**. RF-50 pertenece a una etapa futura
y queda fuera. Un requisito cuenta una sola vez si tiene implementación y
evidencia suficiente registrada; PARCIAL y NO VERIFICADO cuentan cero.
Resultado: **70 verificados / 74 = 94,59 %**, tres parciales y uno no verificado.
No se pondera por prioridad ni por número de pruebas. Los 49 RF tienen evidencia
asociada; los límites restantes están enumerados en el punto 12.

El mecanismo de aceptación de políticas está probado, pero no se interpreta
como certificación jurídica del contenido. La revisión de normalización incluye
excepciones técnicas documentadas. La cifra no es cobertura de código, progreso
del Excel ni aceptación académica. [trazabilidad.json](trazabilidad.json) permite
recalcularla; [MATRIZ.md](MATRIZ.md) vincula cada requisito con código y pruebas.
