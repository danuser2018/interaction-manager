# Registro de cambios

Todos los cambios notables de este proyecto se documentan en este fichero.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## Guía de uso

Cada versión se documenta bajo su número de versión y fecha de publicación.
Los cambios se agrupan en las siguientes categorías:

- **Añadido** — nuevas funcionalidades.
- **Cambiado** — cambios en funcionalidades existentes.
- **Obsoleto** — funcionalidades que serán eliminadas en versiones futuras.
- **Eliminado** — funcionalidades eliminadas en esta versión.
- **Corregido** — corrección de errores.
- **Seguridad** — correcciones de vulnerabilidades.

---

## [1.0.0] 2026-06-04

### Añadido

- Implementación completa del servicio `interaction-manager` con clientes HTTP, pipeline de orquestación, y watcher de ficheros.
- Configuración de Docker (`Dockerfile`, `docker-compose.yml`).
- Configuración de GitHub Actions para CI (`.github/workflows/pr-tests.yml`).
- Pruebas unitarias para la lógica principal.
- Fichero `CONTRIBUTING.md` con el flujo de trabajo Trunk Based Development,
  convenciones de commits, guía de Pull Requests y buenas prácticas para
  desarrollo asistido con IA.
- Fichero `CHANGELOG.md` con el formato Keep a Changelog v1.1.0 en castellano.

### Cambiado

- Aumentado el timeout del cliente HTTP a 60 segundos en `stt_client.py` para soportar audios más largos.

### Corregido

- Corregido el nombre del parámetro de `file` a `audio` en `stt_client.py` para coincidir con la API de STT.
- Corregido el mock de la respuesta HTTP en las pruebas de `stt_client.py` y `orchestrator_client.py` para evitar errores `AttributeError: 'coroutine' object has no attribute 'get'` durante la ejecución de pytest en la pipeline.

## Sin publicar

---

<!-- Plantilla para nuevas versiones:

## [X.Y.Z] - AAAA-MM-DD

### Añadido
-

### Cambiado
-

### Obsoleto
-

### Eliminado
-

### Corregido
-

### Seguridad
-

-->

[Sin publicar]: https://github.com/danuser2018/tts-capability/compare/HEAD...HEAD
