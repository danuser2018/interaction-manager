# UX Audio Feedback Implementation

## Context

Nova-2 ya dispone de un modelo de interacción definido en:

* UX_INTERACTION_GUIDE.md
* TONE_GUIDE.md

Uno de los principios fundamentales del sistema es:

> El usuario debe saber siempre que ha sido escuchado.

Actualmente existe una ventana de incertidumbre entre el final de la captura de voz y la recepción de la transcripción STT.

Durante este periodo:

```text
Usuario termina de hablar
        ↓
Silencio
        ↓
STT finaliza
        ↓
Procesamiento continúa
```

Aunque el sistema esté funcionando correctamente, el usuario puede percibir que:

* Nova-2 no ha escuchado la petición.
* La captura de audio ha fallado.
* El sistema se ha bloqueado.
* Debe repetir la petición.

Este comportamiento contradice los objetivos definidos en el UX Guide.

---

## Objetivo

Reducir la incertidumbre inicial durante la fase de reconocimiento de voz.

Nova-2 debe proporcionar una confirmación inmediata de recepción de la petición.

La implementación debe mejorar la percepción de velocidad sin modificar el pipeline funcional existente.

---

## Recursos disponibles

Se han incorporado dos audios al repositorio:

```text
audio/system/
├── acknowledge.wav
└── waiting.wav
```

### acknowledge.wav

Audio breve de confirmación.

Significado UX:

> "He recibido tu petición."

---

### waiting.wav

Textura sonora de espera.

Significado UX:

> "La petición está siendo procesada."

No representa progreso.

No representa tiempo restante.

Únicamente comunica actividad.

---

## Comportamiento esperado

### Flujo normal

```text
Usuario termina de hablar
        ↓
acknowledge.wav
        ↓
waiting.wav
        ↓
Inicio STT
        ↓
STT finaliza
        ↓
waiting.wav OFF
        ↓
Resto del pipeline
```

---

## Reglas UX

### Regla 1

acknowledge.wav debe reproducirse inmediatamente tras finalizar la captura de voz.

Objetivo:

Eliminar incertidumbre.

---

### Regla 2

waiting.wav debe comenzar inmediatamente después de la confirmación.

Objetivo:

Ocultar el silencio durante la fase STT.

---

### Regla 3

waiting.wav debe detenerse en cuanto exista una respuesta válida del STT.

No debe permanecer activo durante:

* Clasificación de intención.
* Selección de plugin.
* Ejecución del plugin.
* Generación TTS.

El UX Guide define explícitamente que el audio de espera cubre únicamente la fase STT.

---

### Regla 4

Si el STT finaliza rápidamente, el sistema puede omitir waiting.wav.

No debe forzarse una duración mínima artificial.

Priorizar siempre la rapidez percibida.

---

### Regla 5

La reproducción de estos audios no debe bloquear el pipeline principal.

El procesamiento debe continuar independientemente de la reproducción.

---

## Casos de error

### Error STT

```text
acknowledge.wav
        ↓
waiting.wav
        ↓
Error STT
        ↓
waiting.wav OFF
        ↓
Mensaje de error
```

---

### Timeout STT

```text
acknowledge.wav
        ↓
waiting.wav
        ↓
Timeout
        ↓
waiting.wav OFF
        ↓
Mensaje de error
```

---

### Texto vacío

```text
acknowledge.wav
        ↓
waiting.wav
        ↓
Transcripción vacía
        ↓
waiting.wav OFF
        ↓
"No entendido."
```

---

## Responsabilidad arquitectónica

La gestión de estos audios pertenece exclusivamente al Interaction Manager.

No debe trasladarse responsabilidad a:

* STT Service
* Orchestrator
* Plugins
* TTS Service

El feedback de interacción forma parte de la capa UX del sistema.

---

## Configuración

Las rutas de los audios deben centralizarse como configuración del Interaction Manager.

Se recomienda evitar rutas hardcodeadas dentro del código de negocio.

Ejemplo:

```text
audio/system/acknowledge.wav
audio/system/waiting.wav
```

---

## Logging

Registrar:

* Inicio de reproducción acknowledge.
* Inicio de reproducción waiting.
* Fin de reproducción waiting.

No registrar:

* Contenido del audio.
* Información sensible.

---

## Criterios de aceptación

### CA-001

Toda petición válida reproduce acknowledge.wav inmediatamente después de finalizar la captura.

---

### CA-002

Durante la fase STT no existe silencio perceptible para el usuario.

---

### CA-003

waiting.wav se detiene automáticamente cuando finaliza el STT.

---

### CA-004

La reproducción de audios no bloquea el pipeline principal.

---

### CA-005

La funcionalidad continúa operativa cuando existen errores de STT.

---

### CA-006

La experiencia es consistente con las reglas definidas en UX_INTERACTION_GUIDE.md.

---

## Resultado esperado

La interacción percibida por el usuario pasa de:

```text
Hablar
    ↓
Silencio
    ↓
Respuesta
```

a:

```text
Hablar
    ↓
Confirmación
    ↓
Espera guiada
    ↓
Respuesta
```

La latencia real permanece inalterada.

La latencia percibida se reduce significativamente.

El usuario sabe en todo momento que Nova-2 ha recibido la petición y está trabajando en ella.
