# Refinamiento de Feature: Audio de Emergencia Único

**Documento de origen:** [unique_emergency_audio.md](file:///home/danuser2018/workspace/interaction-manager/docs/features/unique_emergency_audio.md)

---

## 1. Resumen y Contexto de Negocio

El sistema Nova-2 cuenta actualmente con un Interaction Manager que coordina el flujo de interacción de voz. Si ocurre un fallo en alguna etapa del flujo (Speech-to-Text, Orchestrator o Text-to-Speech), el sistema debe reproducir un audio local de emergencia para evitar silencios ambiguos para el usuario.
Actualmente, el Interaction Manager gestiona cinco archivos de audio específicos para distintos tipos de error.
El objetivo de esta funcionalidad es simplificar este mecanismo, sustituyendo el catálogo de audios por un único archivo de audio de emergencia (`emergency.wav`). Este cambio reduce la complejidad del sistema y el coste de mantenimiento de los recursos de audio local sin afectar al diagnóstico interno de errores ni al flujo general de comunicación.

---

## 2. Análisis de Servicios e Impacto

| Servicio | Impacto | Descripción del Cambio |
| :--- | :--- | :--- |
| `interaction-manager` | Modificar | 1. Modificar `app/services/error_handler.py` para utilizar un único archivo de audio `emergency.wav` en caso de fallo en TTS o error relacionado con el mismo.<br>2. Eliminar los archivos de audio redundantes del directorio `audio/emergency/` (`fatal_error.wav`, `service_unavailable.wav`, `stt_not_understood.wav`, `stt_unavailable.wav` y `operation_failed.wav` tras la copia).<br>3. Agregar el nuevo archivo `emergency.wav` (basado en el actual `operation_failed.wav`).<br>4. Actualizar las pruebas unitarias en `tests/test_error_handler.py` para adaptarlas al nuevo comportamiento simplificado. |
| `stt-capability` | Ninguno | Sin impacto. El servicio de reconocimiento de voz no se ve afectado. |
| `orchestrator` | Ninguno | Sin impacto. El orquestador no se ve afectado. |
| `tts-capability` | Ninguno | Sin impacto. El servicio de síntesis de voz no se ve afectado. |
| `speaker-watchdog` | Ninguno | Sin impacto. Reproduce cualquier archivo `.wav` depositado en el directorio de salida de forma genérica. |

---

## 3. Especificación de Comportamiento (Criterios de Aceptación)

### Escenario 1: Reproducción de audio de emergencia único ante fallo en la síntesis de voz para errores no relacionados con TTS
```gherkin
Dado que el pipeline de interacción falla con un error de tipo STTEmptyTranscriptionError
Y el Interaction Manager traduce el error al mensaje de experiencia de usuario "No he entendido lo que has dicho."
Cuando el Interaction Manager intenta sintetizar dicho mensaje mediante TTSClient y se produce una excepción
Entonces el Interaction Manager debe capturar la excepción y cargar el archivo local emergency.wav
Y debe retornar el contenido binario de emergency.wav para que sea guardado en la ruta de salida.
```

### Escenario 2: Omisión directa de síntesis para excepciones de tipo TTS
```gherkin
Dado que el pipeline de interacción falla con un error de tipo TTSUnavailableError
Cuando el Interaction Manager procesa el error en handle_error
Entonces no debe realizar ninguna llamada a TTSClient.synthesize_speech
Y debe cargar de forma inmediata el archivo local emergency.wav y retornar su contenido binario.
```

### Escenario 3: Conservación del diagnóstico y registro de logs
```gherkin
Dado que ocurre un fallo del tipo STTUnavailableError en el flujo de interacción
Cuando el Interaction Manager procesa el error
Entonces debe registrar el error original STTUnavailableError en los logs con nivel INFO u ERROR
Y debe mover el archivo de audio original al directorio /data/error/
Y debe guardar el archivo final emergency.wav en el directorio /data/output/ con su nombre original de interacción.
```

---

## 4. Diseño Técnico y Contratos

### Estructura de Archivos de Audio Local
Se eliminará el conjunto múltiple de audios y se conservará un único archivo en `audio/emergency/`:
- **Directorio:** `audio/emergency/`
- **Archivo resultante:** `emergency.wav` (Copia exacta de `operation_failed.wav` que tiene el mensaje "No he podido completar la operación.").

### Cambios en Código Fuente

#### Archivo: `app/services/error_handler.py`
Se simplifica el diccionario `ERROR_MAPPING` eliminando la referencia a múltiples archivos y manteniendo únicamente el mensaje de experiencia de usuario (UX message).

```python
# Updated exception mapping to UX messages only
ERROR_MAPPING = {
    STTEmptyTranscriptionError: "No he entendido lo que has dicho.",
    STTNullResponseError: "No he podido completar la operación.",
    STTUnavailableError: "El servicio de reconocimiento de voz no está disponible.",
    OrchestratorResponseError: "No he podido completar la operación.",
    OrchestratorUnavailableError: "El servicio solicitado no está disponible.",
    TTSResponseError: "Ha ocurrido un error interno.",
    TTSUnavailableError: "Ha ocurrido un error interno.",
}
```

La función `handle_error` cargará siempre `emergency.wav` cuando deba recurrir al audio local de contingencia:

```python
async def handle_error(error: Exception) -> bytes:
    """
    Translates an exception to a UX message, attempts TTS synthesis if possible,
    and falls back to a unique pre-recorded emergency audio if TTS fails or is unavailable.
    """
    logger.info(f"Handling error: {error} ({type(error).__name__})")
    
    # Default UX message
    ux_message = "Ha ocurrido un error interno."
    
    # Resolve the UX message from the mapping
    for exc_class, msg in ERROR_MAPPING.items():
        if isinstance(error, exc_class):
            ux_message = msg
            break
            
    logger.debug(f"Translated to UX message: '{ux_message}'")
    
    # Try TTS synthesis unless the error is TTS-related
    if not isinstance(error, (TTSResponseError, TTSUnavailableError)):
        try:
            logger.info(f"Attempting to synthesize error UX message via TTS: '{ux_message}'")
            audio_bytes = await tts_client.synthesize_speech(ux_message)
            if audio_bytes:
                logger.info("Successfully synthesized error UX message via TTS.")
                return audio_bytes
        except Exception as tts_exc:
            logger.warning(f"Failed to synthesize error UX message via TTS: {tts_exc}. Falling back to emergency audio.")
    else:
        logger.info("Error is TTS-related. Bypassing TTS synthesis and using emergency audio directly.")

    # Fallback to the single emergency audio file
    emergency_path = os.path.join(settings.EMERGENCY_AUDIO_DIR, "emergency.wav")
    try:
        logger.info(f"Loading emergency audio from: {emergency_path}")
        with open(emergency_path, "rb") as f:
            return f.read()
    except Exception as read_exc:
        logger.error(f"Failed to read emergency audio file at {emergency_path}: {read_exc}")
        return b""
```

---

## 5. Casos de Borde y Manejo de Errores

| Caso de Borde | Comportamiento Esperado |
| :--- | :--- |
| **Archivo `emergency.wav` no disponible o dañado** | Si el archivo `emergency.wav` no existe en la ruta configurada o no se puede leer, la función `handle_error` capturará el error `read_exc`, registrará un log de error con `logger.error` y retornará `b""` para evitar caídas del servicio. |
| **Excepción genérica o no registrada** | Si ocurre un error no contemplado en `ERROR_MAPPING` (por ejemplo, `ValueError`), se utilizará el mensaje por defecto `"Ha ocurrido un error interno."`. Si la síntesis TTS falla, se utilizará el audio local único `emergency.wav`. |
| **Fallo crítico de entrada/salida (I/O) al escribir el resultado** | Si falla el almacenamiento del archivo de error resultante en `/data/output/`, el error se captura en `file_watcher.py` (con su correspondiente log) para no interrumpir el bucle de eventos del watcher de archivos. |

---

## 6. Estrategia de Testing

- **Tests Unitarios (`pytest`):**
  - Modificar `tests/test_error_handler.py` para adaptar los casos de prueba al nuevo esquema de mapeo y validar que, ante cualquier fallo en la llamada de TTS o ante errores de tipo TTS, el archivo solicitado para su lectura sea estrictamente `emergency.wav`.
  - Comprobar que los mensajes de logs internos se siguen generando correctamente para la trazabilidad y diagnóstico de los errores originales.
- **Tests de Integración:**
  - Ejecutar el pipeline completo simulando respuestas fallidas de los clientes de red (STT, Orchestrator y TTS) y comprobar que el archivo `.wav` guardado en `/data/output/` es exactamente el audio de emergencia único.

---

## 7. Plan de Implementación

- [ ] **Tarea 1 (Assets):** Copiar y renombrar `audio/emergency/operation_failed.wav` a `audio/emergency/emergency.wav`.
- [ ] **Tarea 2 (Assets):** Eliminar los archivos WAV específicos redundantes del directorio `audio/emergency/`: `fatal_error.wav`, `operation_failed.wav`, `service_unavailable.wav`, `stt_not_understood.wav` y `stt_unavailable.wav`.
- [ ] **Tarea 3 (Código):** Modificar `app/services/error_handler.py` adaptando `ERROR_MAPPING` y la lógica de fallback de `handle_error` para usar el archivo `emergency.wav`.
- [ ] **Tarea 4 (Tests):** Actualizar las aserciones e inicializaciones de mock en `tests/test_error_handler.py` para comprobar la carga de `emergency.wav` en todos los flujos de contingencia.
- [ ] **Tarea 5 (Verificación):** Ejecutar los tests unitarios usando `pytest` en el entorno del contenedor o de desarrollo local.
- [ ] **Tarea 6 (Documentación):** Añadir la entrada correspondiente en el `CHANGELOG.md` del repositorio `interaction-manager` bajo la sección `[Sin publicar]`.
- [ ] **Tarea 7 (Documentación):** Añadir una nota de actualización/obsolescencia en `docs/features/error_handling.md` que referencie el nuevo esquema de audio único.
