# Acta PostgreSQL · 22/11/2026

Base temporal creada desde cero con SCRAM. Se aplicó el esquema, se revirtió hasta api.0012 en la base sintética y se volvió a aplicar hasta api.0016. El seed se ejecutó dos veces. El dump se restauró en una segunda base temporal y se contrastaron los recuentos de todas las tablas y los vínculos de resultados y alertas.

Restauración íntegra: 39 tablas, cinco cuentas y dos resultados con alerta.

SASPEL2 verificada: 32 tablas de negocio conservan sus recuentos; recomendaciones históricas privadas.

Dump de demostración conservado localmente en .cache/h4/hito4-demo-20261122.dump de la carpeta oficial SASPEL. SHA-256: FE728F8B29B559711053B0393380B3C1B0D221B1378BEB0AA2A86C5345305055. Contiene solo filas sintéticas. Para usar claves propias en una demostración nueva, ejecutar seed_demo sobre una base dedicada vacía.

El archivo externo SASPEL2C.sql se conservó. La migración aditiva sobre SASPEL2 se precedió de un respaldo privado independiente. La comprobación de integridad física y FK está en INTEGRIDAD.md.
