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
## [1.2.1] 2026-06-23

### Cambiado

- Audio de `interaction.wav` ahora suena un poco más suave.

## [1.2.0] 2026-06-22

### Añadido

- Se añaden audios para confirmación y espera.
- Se añade descripción funcional de como se debe comportar el audio feedback (audios de confirmación y espera).
- Nueva variable de configuración `INTERACTION_AUDIO_FILE` en `app/config/settings.py` para definir la ruta al archivo de audio de feedback.
- Lógica en `app/services/file_watcher.py` para copiar de forma asíncrona no bloqueante el archivo de feedback a la carpeta de salida tras finalizar la captura.
- Lógica de cancelación que elimina el audio de feedback de la carpeta de salida al finalizar el pipeline (con éxito o error) para optimizar la experiencia si el procesamiento es rápido.
- Logs estructurados para registrar el inicio y el fin de reproducción del audio de feedback.

## [1.1.0] 2026-06-20

### Añadido

- Nuevo documento de UX & Interaction guide, que define cómo son las interacciones con el usuario.
- Nuevo documento donde se explica la feature de gestión de errores. 
- Audios pregrabados para errores de usuario.
- Nuevo módulo `app/exceptions.py` con jerarquía de excepciones personalizadas (`STTError`, `OrchestratorError`, `TTSError` y sus subtipos).
- Nuevo módulo `app/services/error_handler.py` que centraliza la traducción de excepciones técnicas a mensajes UX y gestiona la resiliencia mediante audios de emergencia pregrabados.
- Nueva variable de configuración `EMERGENCY_AUDIO_DIR` en `app/config/settings.py` configurable mediante variable de entorno.
- Nuevos tests unitarios para `error_handler` (`tests/test_error_handler.py`) y para los casos de error de los clientes HTTP.

### Cambiado

- `app/clients/stt_client.py`: los fallos HTTP ahora elevan `STTUnavailableError` en lugar de propagar la excepción nativa de `httpx`. El campo `text` se devuelve sin coerción a cadena vacía para distinguir `None` de `""`.
- `app/clients/orchestrator_client.py`: los fallos HTTP elevan `OrchestratorUnavailableError`; las respuestas con `success=false` elevan `OrchestratorResponseError`.
- `app/clients/tts_client.py`: los fallos HTTP elevan `TTSUnavailableError`.
- `app/services/interaction_pipeline.py`: usa las nuevas excepciones específicas en lugar de `ValueError` genérico; diferencia entre transcripción nula y transcripción vacía.
- `app/services/file_watcher.py`: ante cualquier error de pipeline, además de mover el fichero a `/data/error`, genera y escribe un audio de error en `/data/output` para garantizar que el usuario siempre recibe respuesta (RF-001, RF-002, RF-003, RF-004).
- `Dockerfile`: incluye la copia de la carpeta `audio/` para que los audios de emergencia estén disponibles dentro del contenedor.


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
