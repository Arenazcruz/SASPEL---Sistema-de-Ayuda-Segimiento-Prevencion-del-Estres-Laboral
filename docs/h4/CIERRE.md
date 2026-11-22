# Cierre técnico H4 · 22/11/2026

| Verificación | Resultado final |
|---|---|
| Backend y permisos | 445 pruebas aprobadas en 87.535 segundos sobre PostgreSQL aislado, con Edge habilitado y sin omisiones |
| Frontend | 223 pruebas aprobadas y build Angular de producción correcto |
| Navegador | Tres escenarios reales: usuarios y primer acceso, atención entre roles, ensayo del guion con el dataset H4 |
| Django y PostgreSQL | check, migrate --check y makemigrations --check --dry-run correctos contra SASPEL2; migración 0016 aplicada, recuentos conservados |
| Base de demostración | Dataset sembrado dos veces, dump restaurado en otra base y comparado con el original |
| Trazabilidad | Verificadas las 49 rutas de la matriz en el enrutador Django; dependencias y criterios revisados en Cronograma |
| Presentación | Pendiente únicamente presentación/entrega humana externa. |

La versión final está identificada por **hito4-final-20261122** sobre develop. El paquete local **SASPEL-Hito4-20261122.zip** incluye código versionado, documentación, evidencias, pruebas, versión y el dump sintético validado. El archivo VERSION.txt del ZIP identifica el commit exacto. El administrador puede preparar una demo nueva con seed_demo; la contraseña se proporciona al ejecutar el comando.

[Manuales y evidencias](INDICE.md) · [Guion](GUION.md) · [Acta del ensayo](ENSAYO.md) · [Validación de la base](POSTGRES.md).
