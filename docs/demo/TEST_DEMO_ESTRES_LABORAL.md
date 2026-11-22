# Test de demostración sobre estrés laboral — SASPEL

Este cuestionario es original y ficticio, preparado exclusivamente para demostrar la creación, asignación y resolución de un instrumento en SASPEL. **No es una escala validada ni permite medir o diagnosticar estrés laboral.** Sus bandas de puntuación son datos de prueba del software, sin significado clínico. Utilizar cuentas y respuestas sintéticas durante la demostración.

## 1. Datos para crear el instrumento

Ingresar como **Admin o Superadmin** y abrir **Evaluaciones → Instrumentos → Crear instrumento**.

| Campo | Valor para copiar |
| --- | --- |
| Código | `DEMO-EL-08` |
| Nombre | `Estrés laboral — cuestionario de demostración (8 preguntas)` |
| Versión | `1.0` |
| Descripción | `Instrumento ficticio de ocho preguntas para practicar el flujo de creación, asignación y resolución en SASPEL. No validado y sin interpretación clínica.` |
| Es inicial | **No: dejar desmarcado.** |
| Estado final | **Activo**, una vez configurado todo el contenido. |

**Instrucciones para el campo del formulario:**

```text
DEMOSTRACIÓN: utiliza respuestas ficticias. Imagina una semana laboral y señala con qué frecuencia ocurrió cada situación durante los últimos 7 días. Selecciona una sola opción por pregunta: Nunca, Casi nunca, Algunas veces, Frecuentemente o Casi siempre. Responde las ocho preguntas. Puedes guardar el progreso y continuar después. Al finalizar, las respuestas quedan cerradas. El resultado es una banda de prueba del sistema; no mide ni diagnostica estrés laboral.
```

Este instrumento debe ser **no inicial** porque lo asignará el psicólogo a una cuenta que ya tenga el rol **Trabajador**. No sustituye la evaluación inicial del onboarding.

## 2. Crear la escala de respuesta

Abrir **Evaluaciones → Escalas de respuesta → Crear escala**.

| Campo | Valor |
| --- | --- |
| Nombre | `DEMO — Frecuencia laboral 0 a 4` |
| Descripción | `Escala ficticia compartida por las ocho preguntas del instrumento DEMO-EL-08. Valores enteros de 0 a 4, sin inversión.` |
| Estado | Activa |

Entrar a las **opciones de la escala** y crear estas cinco opciones. El orden de presentación y el valor del puntaje son campos distintos.

| Orden | Etiqueta | Valor | Estado |
| --- | --- | --- | --- |
| 1 | Nunca | 0 | Activa |
| 2 | Casi nunca | 1 | Activa |
| 3 | Algunas veces | 2 | Activa |
| 4 | Frecuentemente | 3 | Activa |
| 5 | Casi siempre | 4 | Activa |

Las opciones se crean **una sola vez** en la escala. Las ocho preguntas utilizarán esa misma escala.

## 3. Crear las ocho preguntas

Abrir **Evaluaciones → Preguntas**, seleccionar el instrumento `DEMO-EL-08`, versión `1.0`, y pulsar **Crear pregunta** para cada fila.

Aplicar esta configuración a **todas** las preguntas:

| Campo | Valor |
| --- | --- |
| Tipo de respuesta | `ESCALA` |
| Escala de respuesta | `DEMO — Frecuencia laboral 0 a 4` |
| Respuesta obligatoria | Sí |
| Pregunta invertida | No |
| Estado | Activa |

| Orden | Pregunta: texto para copiar |
| --- | --- |
| 1 | Durante los últimos 7 días, ¿con qué frecuencia sentiste que tenías más tareas de las que podías realizar en tu jornada laboral? |
| 2 | Durante los últimos 7 días, ¿con qué frecuencia sentiste presión por terminar tu trabajo dentro de plazos ajustados? |
| 3 | Durante los últimos 7 días, ¿con qué frecuencia las interrupciones dificultaron que te concentraras en tus tareas laborales? |
| 4 | Durante los últimos 7 días, ¿con qué frecuencia te resultó difícil hacer una pausa durante la jornada laboral? |
| 5 | Durante los últimos 7 días, ¿con qué frecuencia te generó tensión no tener claras las prioridades de tu trabajo? |
| 6 | Durante los últimos 7 días, ¿con qué frecuencia te resultó difícil dejar de pensar en asuntos laborales después de terminar tu jornada? |
| 7 | Durante los últimos 7 días, ¿con qué frecuencia sentiste tensión al comunicarte o coordinar tareas con otras personas en el trabajo? |
| 8 | Durante los últimos 7 días, ¿con qué frecuencia terminaste la jornada sintiendo agotamiento mental relacionado con tus tareas? |

## 4. Crear los rangos de interpretación de demostración

Abrir **Evaluaciones → Rangos de interpretación**, seleccionar el mismo instrumento y crear estos tres rangos activos.

| Orden | Nombre | Puntaje mínimo | Puntaje máximo | Interpretación: texto para copiar |
| --- | --- | --- | --- | --- |
| 1 | Banda A — DEMO | 0 | 10 | Resultado situado en el primer tramo numérico de la demostración. Banda arbitraria utilizada para comprobar la clasificación del software; no expresa un nivel clínico de estrés. |
| 2 | Banda B — DEMO | 11 | 21 | Resultado situado en el segundo tramo numérico de la demostración. Banda arbitraria utilizada para comprobar la clasificación del software; no expresa un nivel clínico de estrés. |
| 3 | Banda C — DEMO | 22 | 32 | Resultado situado en el tercer tramo numérico de la demostración. Banda arbitraria utilizada para comprobar la clasificación del software; no expresa un nivel clínico de estrés. |

**Cómo se calcula:** SASPEL suma los valores de las ocho respuestas. Ninguna pregunta está invertida y no hay ponderaciones adicionales.

```text
Puntaje total = P1 + P2 + P3 + P4 + P5 + P6 + P7 + P8
Mínimo posible = 8 × 0 = 0
Máximo posible = 8 × 4 = 32
```

Los extremos de los rangos son inclusivos. Los puntajes posibles son enteros, por lo que 0–10, 11–21 y 22–32 cubren todos los resultados posibles sin solapamientos. No cambiar el segundo mínimo a 10 ni el tercero a 21: un mismo puntaje coincidiría con dos rangos.

## 5. Revisar antes de asignar

- [ ] Instrumento `DEMO-EL-08`, versión `1.0`, activo y **no inicial**.
- [ ] Una escala activa con cinco opciones activas, valores 0, 1, 2, 3 y 4.
- [ ] Ocho preguntas activas, ordenadas del 1 al 8.
- [ ] Todas son de tipo ESCALA, obligatorias y no invertidas.
- [ ] Todas utilizan la escala `DEMO — Frecuencia laboral 0 a 4`.
- [ ] Tres rangos activos que cubren del 0 al 32 sin coincidencias múltiples.
- [ ] Una cuenta sintética con rol Trabajador y asignación activa al psicólogo de prueba.
- [ ] El psicólogo y el trabajador han completado los pasos de primer acceso que les correspondan.

Si el instrumento se creó activo por defecto, terminar esta configuración antes de asignarlo. Si se desactivó mientras se preparaba, activarlo al finalizar.

## 6. Asignar el test como Psicólogo

1. Cerrar la sesión administrativa e iniciar sesión como **Psicólogo**.
2. Abrir **Mis trabajadores**.
3. Localizar al trabajador sintético que tenga asignado activamente.
4. Pulsar **Asignar instrumentos**.
5. En **Instrumento**, seleccionar `Estrés laboral — cuestionario de demostración (8 preguntas)`, versión `1.0`.
6. Dejar vacía la fecha límite para simplificar la demostración, o indicar una fecha y hora futuras.
7. Pulsar **Asignar**.
8. Comprobar el mensaje **Instrumento asignado** y el estado **PENDIENTE**.

El psicólogo solo puede asignarlo a sus trabajadores autorizados. Si esa misma versión ya tiene una asignación PENDIENTE o EN_PROGRESO para el trabajador, no se permite duplicarla.

## 7. Resolverlo como Trabajador

1. Iniciar sesión con la cuenta del **Trabajador** que recibió la asignación.
2. Abrir **Mis instrumentos**.
3. Localizar el cuestionario y pulsar **Responder**.
4. Pulsar **Comenzar evaluación**.
5. Contestar algunas preguntas con los datos ficticios de la sección siguiente.
6. Pulsar **Guardar progreso**, salir y volver a entrar para demostrar que las respuestas se conservan.
7. Completar las ocho preguntas y pulsar **Finalizar evaluación**.
8. Consultar el resultado y comprobar que coincide con el puntaje esperado.

Guardar progreso mantiene la evaluación abierta. Finalizar la cierra: sus respuestas ya no se pueden modificar. Este test de seguimiento no vuelve a cambiar el rol del trabajador ni repite su onboarding.

## 8. Respuestas ficticias listas para la demostración

Usar esta secuencia para obtener **16 puntos → Banda B — DEMO**:

| Pregunta | Opción que debe seleccionarse | Valor |
| --- | --- | --- |
| 1 | Algunas veces | 2 |
| 2 | Frecuentemente | 3 |
| 3 | Casi nunca | 1 |
| 4 | Algunas veces | 2 |
| 5 | Algunas veces | 2 |
| 6 | Casi nunca | 1 |
| 7 | Frecuentemente | 3 |
| 8 | Algunas veces | 2 |
| **Total esperado** | **Banda B — DEMO** | **16** |

Otros casos para comprobar la clasificación:

| Respuestas ficticias, en orden P1 a P8 | Total | Resultado esperado |
| --- | --- | --- |
| 0, 0, 0, 0, 0, 0, 0, 0 | 0 | Banda A — DEMO |
| 4, 4, 2, 0, 0, 0, 0, 0 | 10 | Banda A — DEMO |
| 4, 4, 3, 0, 0, 0, 0, 0 | 11 | Banda B — DEMO |
| 4, 4, 4, 4, 4, 1, 0, 0 | 21 | Banda B — DEMO |
| 4, 4, 4, 4, 4, 2, 0, 0 | 22 | Banda C — DEMO |
| 4, 4, 4, 4, 4, 4, 4, 4 | 32 | Banda C — DEMO |

Cada caso requiere otra aplicación o cuenta de prueba. No editar respuestas de una aplicación ya finalizada. Después de completar una aplicación, se puede asignar de nuevo la misma versión para demostrar otro resultado.

## 9. Consultar el resultado como Psicólogo

1. Volver a iniciar sesión como el psicólogo asignado.
2. Abrir **Mis trabajadores → Ver resultados** del trabajador de prueba.
3. Localizar el instrumento y comprobar puntaje **16**, banda **B** y fecha.
4. Si se completan dos aplicaciones de la misma versión, abrir **Ver evolución** para comparar los resultados de demostración.

La comparación es numérica y descriptiva. No interpretar las bandas como estrés bajo, moderado o alto ni usar estos resultados para decisiones sobre personas.

## 10. Qué revisar si el procedimiento se detiene

| Situación | Revisar |
| --- | --- |
| No aparece el instrumento al asignar | Está activo, no está marcado como inicial y se guardó correctamente. |
| Se rechaza la asignación por configuración | Hay preguntas activas de tipo ESCALA, una escala activa y opciones activas asociadas. |
| No aparece el trabajador en el panel del psicólogo | Tiene rol Trabajador, cuenta activa y una asignación profesional activa al psicólogo conectado. |
| No se permite una nueva asignación | No existe otra asignación pendiente o en progreso de la misma versión para esa persona. |
| No permite finalizar | Se contestaron todas las preguntas obligatorias con opciones de sus escalas. |
| El resultado no tiene banda o hay rangos coincidentes | Se seleccionó el instrumento correcto al crear los rangos y se copiaron los límites 0–10, 11–21 y 22–32. |
| No permite editar el contenido | La versión ya tiene aplicaciones. Para cambiar preguntas o puntuación, preparar una nueva versión y usar otra escala si se modifican sus opciones. |

## Relación con el cronograma

La creación administrativa del instrumento corresponde a **T25**. La asignación desde el psicólogo corresponde a **T47**, programada del **31/10 al 02/11/2026**, y la evolución corresponde a **T49**, del **03 al 06/11/2026**. Estas funciones ya están implementadas en la versión actual; al presentar un corte al 26/10/2026 deben identificarse como adelantos del cronograma.

**Resultado que debes mostrar:** Admin crea el instrumento y su contenido → Psicólogo lo asigna → Trabajador guarda y finaliza → SASPEL calcula 16 puntos y muestra Banda B — DEMO → Psicólogo consulta el resultado autorizado.
