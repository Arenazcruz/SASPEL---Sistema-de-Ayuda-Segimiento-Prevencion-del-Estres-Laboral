# Estrategia de ramas de SASPEL

## main

Versión estable, funcionando y presentable. Es la rama que puede revisar el
docente para conocer el estado estable de SASPEL. Recibe cambios probados
desde `develop`, preferentemente mediante Pull Request (PR).

## develop

Integración de funcionalidades terminadas. Aquí se unen las ramas `feature/*`
y se ejecutan las pruebas de integración antes de preparar una entrega a `main`.

## feature/*

Desarrollo aislado de funcionalidades. Cada rama se crea desde `develop`.
La primera es `feature/asignacion-profesional`, reservada para
**T23 - Asignación Psicólogo-Trabajador**. Su creación no implementa T23.

Otras ramas futuras pueden ser `feature/instrumentos`, `feature/citas`,
`feature/seguimiento` y `feature/reportes`.

```text
feature/*
    ↓ PR + pruebas
develop
    ↓ PR + pruebas de integración
main
```

**REGLA: No desarrollar directamente nuevas funcionalidades en main.**

## Trabajo por módulo

1. Actualizar `develop`: `git switch develop` y `git pull --ff-only origin develop`.
2. Crear la rama: `git switch -c feature/nombre-funcionalidad`.
3. Desarrollar únicamente la funcionalidad de esa rama.
4. Ejecutar las pruebas del backend y frontend indicadas en el README.
5. Revisar los archivos y crear un commit con un mensaje claro.
6. Publicar: `git push -u origin feature/nombre-funcionalidad`.
7. Abrir un PR de la feature hacia `develop`, revisar e integrar.
8. Verificar el conjunto en `develop`, incluyendo pruebas de integración.
9. Cuando esté estable, abrir un PR de `develop` hacia `main` e integrar.

Si una verificación falla, detener la entrega, informar el problema y corregirlo
en la rama de trabajo antes de integrar una versión estable.

## Próximo trabajo: T23

La rama ya preparada se utiliza con:

```powershell
git switch feature/asignacion-profesional
git pull --ff-only origin feature/asignacion-profesional
```

Cuando T23 esté desarrollada y probada, el flujo será:

```text
feature/asignacion-profesional → PR → develop → pruebas de integración → PR → main
```

Inicialmente las tres ramas pueden apuntar al mismo commit. No se crean cambios
inútiles para diferenciarlas, ni PR vacíos. Los PR con cambios reales permiten
al docente revisar qué cambió, cuándo, en qué rama y mediante cuáles commits.

## Mensajes de commits e hitos

Usar mensajes que describan el cambio:

- `feat: implementar asignación profesional`
- `feat: agregar CRUD de instrumentos`
- `fix: corregir validación de citas`
- `test: agregar pruebas de autenticación`
- `docs: actualizar guía Postman`
- `refactor: simplificar repositorio de usuarios`

Evitar mensajes como `cambios`, `prueba`, `final2` o `rama 3`.
Los tags `hito-2`, `hito-3` o `hito-4` se reservarán para entregas reales;
la preparación inicial de ramas no necesita tags.

## Revisión antes de publicar

Revisar `git status --short`, `git diff` y, después de añadir archivos,
`git diff --cached`. Confirmar que `.env` está ignorado con
`git check-ignore .env`; solo `.env.example` puede versionarse.
No incluir credenciales, bases reales, dumps, ZIP, dependencias, entornos
virtuales, cachés ni evidencias con información personal.
Nunca usar `git push --force` como parte del flujo normal.

Este documento define el acuerdo de trabajo. No sustituye reglas de protección
de ramas configuradas en GitHub.
