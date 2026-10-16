# T32 · Informe de pruebas pre-H3

Verificado el 16/10/2026 sobre develop con T29 (962698d) y T31 (6cadd1a).

| Escenario | Evidencia ejecutable | Resultado |
| --- | --- | --- |
| Login JWT, identidad y permisos actualizados | test_auth_api, test_primer_acceso | Aprobado |
| Gestión de usuarios y asignaciones | test_superadmin_api, test_assignments_api, test_area_cargo_api | Aprobado |
| Instrumentos, respuestas, puntuación y finalización | test_instruments_api, test_instrument_content_api, test_responder_evaluacion, test_cierre_onboarding | Aprobado |
| Resultado persistido e historial autorizado | test_resultados_historial | Aprobado |
| Solicitud, confirmación, rechazo, cancelación, concurrencia | test_citas_api | Aprobado |
| Login → evaluación → transición de rol → resultado → profesional → cita → cancelación | test_integracion_nucleo | Aprobado |
| Revocación de asignación corta resultados y citas del profesional | test_integracion_nucleo | Aprobado |

Desde backend: `python manage.py test tests.test_integracion_nucleo --noinput`: 2/2. Suite completa `python manage.py test tests --noinput`: 354 descubiertas, 353 aprobadas, 1 omitida (navegador optativo requiere Angular/Playwright). Pruebas HTTP con JWT y PostgreSQL temporal test_SASPEL2, sin mocks de negocio. No modifica registros de SASPEL2.

Frontend: `npm test -- --watch=false`, 179/179 aprobadas en 14 archivos; `npm run build` aprobado sobre el mismo código productivo integrado en T31. Los componentes usan HttpTestingController; no son E2E de navegador. La validación E2E integral corresponde a T55, fuera de este corte.

Sin bloqueadores funcionales detectados en estos escenarios. Actualización documental: T08 queda Completado con el nuevo criterio expresamente autorizado; la reconstrucción lógica y sus límites se registran en [T16](T16_PAQUETE_HITO2.md#t08--línea-base-lógica-y-límites-de-la-evidencia). SASPEL2C.sql contiene 28 CREATE TABLE, incluidas tablas de negocio, y no demuestra la línea base física histórica de solo tablas técnicas. Inspección únicamente en lectura; no se ejecutó ni restauró. SHA-256: a96349eb27d5c33823cdb51922f54ce5c566566647e788e3144bfca8b2a787a1.
