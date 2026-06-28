# Nova-2 UX & Interaction Guide

## 1. Objetivo

Este documento define la experiencia de interacción de Nova-2 desde la perspectiva del usuario.

Mientras que el Tone Guide define qué debe decir Nova-2, este documento define:

- Cuándo debe responder.
- Cómo debe gestionar las esperas.
- Cómo debe comunicar el estado del sistema.
- Cómo debe minimizar la fricción durante la interacción.

El objetivo es que Nova-2 se perciba como un sistema:

- Rápido.
- Fiable.
- Reactivo.
- Predecible.

Incluso cuando la ejecución real requiera varios segundos.

---

# 2. Principio fundamental

La percepción de velocidad es más importante que la velocidad real.

El usuario debe saber siempre:

1. Que ha sido escuchado.
2. Que la petición ha sido comprendida.
3. Que la acción está siendo ejecutada.
4. Que recibirá el resultado cuando esté disponible.

La incertidumbre genera más frustración que la espera.

---

# 3. Arquitectura de interacción

La interacción completa se divide en varias fases.

```text
Usuario habla
        ↓
Petición recibida
        ↓
STT
        ↓
Clasificación de intención
        ↓
Ejecución
        ↓
Respuesta
```

Cada fase tiene reglas específicas de UX.

---

# 4. Fase 1: Petición recibida

## Objetivo

Eliminar la incertidumbre inicial.

El usuario debe percibir inmediatamente que Nova-2 ha recibido la petición.

---

## Comportamiento

Al finalizar la captura de voz:

```text
Usuario termina de hablar
        ↓
Audio de espera ON
```

---

## Audio de espera

Nova-2 utiliza una textura sonora suave para indicar:

> "Te he escuchado."

El audio NO representa progreso.

El audio NO representa tiempo restante.

El audio únicamente indica que el sistema ha recibido la petición.

---

## Características del audio

Debe ser:

- Suave.
- Discreto.
- No verbal.
- No musicalmente dominante.
- Sin ritmo marcado.
- Sin voz.

Debe evitar:

- Sonidos de error.
- Música de espera telefónica.
- Melodías reconocibles.
- Elementos que distraigan al usuario.

---

## Duración

El audio permanece activo durante toda la pipeline de ejecución (STT -> Orchestrator -> TTS), deteniéndose en cuanto exista una respuesta válida del TTS.

---

# 5. Fase 2: Comprensión y Ejecución

## Objetivo

Interpretar la intención del usuario y procesar la petición.

Durante esta fase, el audio de espera continúa activo para ocultar el silencio durante el procesamiento técnico del sistema.

```text
STT completado
        ↓
Procesamiento Orchestrator
        ↓
Generación TTS completada
        ↓
Audio de espera OFF
```

---

# 6. Reglas de Duración y Asincronía

## Duración máxima
Las operaciones síncronas de Nova-2 no deben tener una duración mayor a 10 segundos.

## Operaciones largas
Si la operación requiere una ejecución que supere los 10 segundos:
1. Se debe derivar la respuesta a un canal asíncrono secundario (como puede ser el correo electrónico).
2. Responder inmediatamente al usuario en la interacción de voz indicando que la respuesta se enviará por dicho canal alternativo cuando esté lista.

### Flujo de operación larga
```text
Petición recibida
        ↓
Detección de proceso largo (> 10s)
        ↓
Respuesta inmediata por voz ("Enviaré el resultado por correo en cuanto esté listo.")
        ↓
Ejecución en segundo plano
        ↓
Envío del correo con el resultado
```

### Mensajes recomendados para operaciones largas
- "El proceso tardará un momento, te enviaré los detalles por correo cuando finalice."
- "He iniciado la tarea. Te mandaré el resultado por e-mail en cuanto termine."

---

# 7. Gestión de errores

Los errores deben comunicarse inmediatamente.

No deben existir estados ambiguos.

---

## Correcto

- "No he podido hacerlo."
- "Servicio no disponible."
- "La operación ha fallado."

---

## Incorrecto

- Mantener silencio.
- Esperar indefinidamente.
- Reproducir audio de espera sin finalizar.

---

# 8. Silencio como herramienta UX

El silencio es una herramienta válida.

Nova-2 no debe emitir sonidos o mensajes innecesarios.

Si una respuesta puede producirse inmediatamente:

```text
Petición
        ↓
Respuesta
```

No debe añadirse ninguna capa adicional.

---

# 9. Consistencia

Todas las interacciones deben seguir este modelo independientemente del plugin utilizado.

El usuario debe percibir una experiencia uniforme.

La diferencia entre plugins debe estar en la funcionalidad.

Nunca en la experiencia de interacción.

---

# 10. Evolución futura

Este modelo está diseñado para Nova-2.

Las futuras iteraciones (Nova-3 y posteriores) podrán incorporar:

- Conversaciones multi-turno.
- Contexto persistente.
- MCPs.
- Agentes especializados.

Sin embargo, deberán mantener los principios fundamentales:

- Reducir incertidumbre.
- Minimizar fricción.
- Comunicar estado.
- Evitar esperas ambiguas.

---

# 11. Resumen

Nova-2 debe garantizar que el usuario siempre sepa:

- Que ha sido escuchado.
- Que la petición ha sido comprendida.
- Que la acción está en marcha.
- Que recibirá el resultado cuando corresponda.

La misión de Nova-2 no es conversar.

La misión de Nova-2 es transmitir confianza operativa.
