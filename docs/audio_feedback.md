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

Se ha incorporado un audio al repositorio:

```text
audio/system/interaction.wav
```

Este audio incorpora dos sonidos:

### Sonido breve de confirmación

Significado UX:

> "He recibido tu petición."

---

### Textura sonora de espera.

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
interaction.wav
        ↓
Inicio STT
        ↓
STT finaliza
        ↓
orchestrator resuelve        
        ↓
TTS finaliza
        ↓
interaction.wav OFF
        ↓
Se reproduce respuesta
```

---

## Reglas UX

### Regla 1

interaction.wav debe reproducirse inmediatamente tras finalizar la captura de voz.

Objetivo:

Eliminar incertidumbre.

---

### Regla 2

interaction.wav debe continuar hasta tener respuesta disponible.

Objetivo:

Ocultar el silencio durante la fase STT-orchestrator-TTS

---

### Regla 3

interaction.wav debe detenerse en cuanto exista una respuesta válida del TTS.

---

### Regla 4

Si la pipeline finaliza rápidamente, el sistema puede omitir interaction.wav.

No debe forzarse una duración mínima artificial.

Priorizar siempre la rapidez percibida.

---

### Regla 5

La reproducción de este audio no debe bloquear el pipeline principal.

El procesamiento debe continuar independientemente de la reproducción.

---

## Casos de error

### Error STT

```text
interaction.wav
        ↓
Error STT
        ↓
interaction.wav OFF
        ↓
Mensaje de error
```

---

### Timeout STT

```text
interaction.wav
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
interaction.wav
        ↓
Transcripción vacía
        ↓
interaction.wav OFF
        ↓
"No entendido."
```

---

## Responsabilidad arquitectónica

La gestión de este audio pertenece exclusivamente al Interaction Manager.

No debe trasladarse responsabilidad a:

* STT Service
* Orchestrator
* Plugins
* TTS Service

El feedback de interacción forma parte de la capa UX del sistema.

---

## Configuración

La ruta del audio debe centralizarse como configuración del Interaction Manager.

Se recomienda evitar rutas hardcodeadas dentro del código de negocio.

Ejemplo:

```text
audio/system/interaction.wav
```

---

## Logging

Registrar:

* Inicio de reproducción interaction.wav
* Fin de reproducción interaction.wav

No registrar:

* Contenido del audio.
* Información sensible.

---

## Criterios de aceptación

### CA-001

Toda petición válida reproduce interaction.wav inmediatamente después de finalizar la captura.

---

### CA-002

Durante la ejecución de la pipeline no existe silencio perceptible para el usuario.

---

### CA-003

interaction.wav se detiene automáticamente cuando hay respuesta.

---

### CA-004

La reproducción del audio no bloquea el pipeline principal.

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
