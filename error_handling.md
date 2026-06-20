# Error Handling UX Alignment

## Context

Nova-2 dispone actualmente de un Interaction Manager responsable de coordinar el flujo:

```text
Audio
  ↓
STT
  ↓
Orchestrator
  ↓
TTS
  ↓
Respuesta al usuario
```

La gestión técnica de errores ya existe.

Cuando ocurre un error durante:

* STT
* Orchestrator
* TTS

el archivo original es movido a:

```text
/data/error
```

Sin embargo, actualmente existen escenarios donde el usuario no recibe ninguna respuesta.

Ejemplo:

* El STT devuelve texto vacío.
* El STT devuelve null.
* El STT produce una excepción.
* El servicio STT no responde.

En estos casos el audio se mueve correctamente a `/data/error`, pero Nova-2 permanece en silencio.

Esto genera incertidumbre y contradice los principios UX definidos en:

`UX_INTERACTION_GUIDE.md`

---

## Problema

Actualmente existe una diferencia entre:

### Gestión técnica del error

El sistema detecta el fallo y preserva el audio.

### Gestión UX del error

El usuario no recibe confirmación de que la petición ha fallado.

El resultado es una interacción ambigua.

Desde la perspectiva del usuario:

```text
Hablo
    ↓
Espero
    ↓
Silencio
```

El usuario no sabe si:

* Nova no ha escuchado.
* Nova está procesando.
* Nova se ha bloqueado.
* El servicio STT ha fallado.
* Debe repetir la petición.

---

## Objetivo

Garantizar que toda interacción produzca una respuesta final.

No deben existir flujos que terminen en silencio.

La regla es:

```text
Audio recibido
        ↓
Procesamiento
        ↓
Resultado o error
        ↓
Respuesta al usuario
```

---

## Principio arquitectónico

El Interaction Manager es responsable de la experiencia de interacción.

Por tanto:

* Debe seguir moviendo archivos a `/data/error`.
* Debe seguir registrando logs.
* Debe seguir preservando evidencias para diagnóstico.

Pero además:

* Debe generar una respuesta audible para el usuario.

La gestión UX del error pertenece al Interaction Manager.

No debe delegarse al STT, Orchestrator ni TTS.

---

## Comportamiento esperado

### STT devuelve texto vacío

Respuesta:

```text
No he entendido lo que has dicho.
```

---

### STT devuelve null

Respuesta:

```text
No he podido procesar el audio.
```

---

### Timeout STT

Respuesta:

```text
El servicio de reconocimiento de voz no está disponible.
```

---

### Error del Orchestrator

Respuesta:

```text
No he podido completar la operación.
```

---

### Error del TTS

Si es posible generar audio alternativo:

```text
Ha ocurrido un error al generar la respuesta.
```

Si no es posible generar audio:

* Registrar error.
* Mover a `/error`.

Este es el único escenario donde podría no existir respuesta audible.

---

## Requisitos funcionales

### RF-001

Toda interacción debe finalizar en uno de dos estados:

```text
SUCCESS
ERROR
```

---

### RF-002

Tanto SUCCESS como ERROR deben producir un mensaje final para el usuario.

---

### RF-003

Los errores deben transformarse en mensajes UX antes de abandonar el pipeline.

---

### RF-004

El movimiento a `/data/error` no debe sustituir la comunicación al usuario.

Ambas acciones deben coexistir.

---

## Requisitos de diseño

La implementación debe minimizar cambios en la arquitectura actual.

Se recomienda:

* Centralizar la traducción de excepciones a mensajes UX.
* Mantener un catálogo simple de mensajes de error.
* Evitar que cada cliente HTTP gestione sus propios mensajes.

El Interaction Manager debe ser la única capa responsable de la comunicación final con el usuario.

---

## Criterio de aceptación principal

No debe existir ningún escenario conocido en el que un usuario emita una petición y Nova-2 permanezca en silencio sin comunicar el resultado de la operación.

## Estrategia de resiliencia para TTS

### Contexto

La arquitectura propuesta asume que todos los errores deben comunicarse al usuario.

Sin embargo, existe un escenario especial:

```text
Audio
    ↓
STT
    ↓
Orchestrator
    ↓
TTS
    ↓
Respuesta
```

Si el servicio TTS falla, Nova-2 pierde su mecanismo principal para comunicar errores.

Esto puede provocar nuevamente un estado ambiguo para el usuario.

---

## Objetivo

Garantizar que Nova-2 pueda comunicar errores incluso cuando el servicio TTS no esté disponible.

---

## Requisito arquitectónico

El Interaction Manager debe disponer de un conjunto de audios de emergencia pregrabados.

Estos audios no dependerán de:

* STT
* Orchestrator
* TTS
* Servicios externos

Deben estar disponibles localmente dentro del propio servicio.

---

## Emergency Audio Pack

Se recomienda incluir un conjunto mínimo de mensajes de contingencia.

Ejemplos:

```text
audio/emergency/
├── stt_not_understood.wav
├── stt_unavailable.wav
├── operation_failed.wav
├── service_unavailable.wav
└── fatal_error.wav
```

---

## Comportamiento esperado

### Caso normal

```text
Petición
    ↓
TTS disponible
    ↓
Respuesta sintetizada
```

---

### Caso degradado

```text
Petición
    ↓
TTS falla
    ↓
Audio de emergencia
```

---

## Mensajes recomendados

### Audio: stt_not_understood.wav

```text
No he entendido lo que has dicho.
```

---

### Audio: stt_unavailable.wav

```text
El servicio de reconocimiento de voz no está disponible.
```

---

### Audio: operation_failed.wav

```text
No he podido completar la operación.
```

---

### Audio: service_unavailable.wav

```text
El servicio solicitado no está disponible.
```

---

### Audio: fatal_error.wav

```text
Ha ocurrido un error interno.
```

---

## Generación de audios

Los audios deben generarse previamente durante el despliegue o construcción del sistema.

No deben sintetizarse dinámicamente durante la ejecución.

Esto garantiza que permanezcan disponibles incluso si el servicio TTS está caído.

---

## Responsabilidad

La selección y reproducción de audios de emergencia corresponde exclusivamente al Interaction Manager.

Ni el STT ni el Orchestrator deben conocer esta funcionalidad.

---

## Criterio de aceptación adicional

Nova-2 debe mantener capacidad de respuesta audible incluso ante una caída completa del servicio TTS.

El usuario no debe percibir silencio como consecuencia de un fallo interno.

La regla final es:

```text
Toda petición produce una respuesta.

Si no es posible generar una respuesta normal,
debe emitirse una respuesta de emergencia.
```
