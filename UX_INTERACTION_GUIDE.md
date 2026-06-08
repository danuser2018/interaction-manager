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

El audio permanece activo exclusivamente durante el procesamiento STT.

---

# 5. Fase 2: Comprensión

## Objetivo

Interpretar la intención del usuario.

Cuando el STT finaliza:

```text
STT completado
        ↓
Audio OFF
        ↓
Router
        ↓
Selección de plugin
```

A partir de este momento Nova-2 conoce la intención solicitada.

---

# 6. Clasificación de operaciones

Tras seleccionar el plugin, Nova-2 clasifica la operación según su duración estimada.

Se distinguen tres categorías:

- Operación corta.
- Operación media.
- Operación larga.

---

# 7. Operaciones cortas

## Definición

Duración esperada inferior a 1 segundo.

Ejemplos:

- Encender una luz.
- Apagar un dispositivo.
- Abrir una aplicación.
- Consultar la hora.
- Obtener información local ya disponible.

---

## Flujo

```text
Audio ON
        ↓
STT
        ↓
Audio OFF
        ↓
Respuesta inmediata
```

---

## Ejemplos

Usuario:

> Enciende la luz.

Nova-2:

> Luz encendida.

---

Usuario:

> ¿Qué hora es?

Nova-2:

> Son las 15:42.

---

## Regla

No utilizar confirmaciones adicionales.

No utilizar coletillas.

La respuesta final es suficiente.

---

# 8. Operaciones medias

## Definición

Duración esperada entre 1 y 10 segundos.

Ejemplos:

- Consultar APIs externas.
- Consultar información remota.
- Obtener estados de servicios externos.
- Búsquedas simples.

---

## Flujo

```text
Audio ON
        ↓
STT
        ↓
Audio OFF
        ↓
Confirmación breve
        ↓
Resultado
```

---

## Objetivo

Reducir incertidumbre durante la espera adicional.

---

## Confirmaciones válidas

Las confirmaciones deben indicar acción.

Ejemplos:

- "Consultándolo."
- "Comprobándolo."
- "Buscando información."
- "Revisándolo."

---

## Confirmaciones no válidas

Evitar:

- "Procesando petición."
- "Cargando."
- "Espere."
- "Un momento." (salvo casos excepcionales)

Las confirmaciones deben reflejar la acción realizada.

---

## Ejemplo

Usuario:

> ¿Qué tiempo hace?

Nova-2:

> Consultándolo.

(...)

> 22 grados.

---

# 9. Operaciones largas

## Definición

Duración esperada superior a 10 segundos.

Ejemplos:

- Actualizaciones.
- Automatizaciones complejas.
- Procesos de mantenimiento.
- Análisis extensos.
- Futuros procesos MCP.

---

## Flujo

```text
Audio ON
        ↓
STT
        ↓
Audio OFF
        ↓
Aceptación
        ↓
Ejecución asíncrona
        ↓
Notificación posterior
```

---

## Objetivo

Evitar bloquear al usuario.

Nova-2 no debe mantener una espera larga abierta.

---

## Mensajes válidos

- "He comenzado la tarea."
- "La operación está en marcha."
- "Te avisaré cuando termine."

---

## Regla

La conversación termina aquí.

El resultado llegará posteriormente mediante el canal correspondiente.

---

# 10. Gestión de errores

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

# 11. Silencio como herramienta UX

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

# 12. Consistencia

Todas las interacciones deben seguir este modelo independientemente del plugin utilizado.

El usuario debe percibir una experiencia uniforme.

La diferencia entre plugins debe estar en la funcionalidad.

Nunca en la experiencia de interacción.

---

# 13. Evolución futura

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

# 14. Resumen

Nova-2 debe garantizar que el usuario siempre sepa:

- Que ha sido escuchado.
- Que la petición ha sido comprendida.
- Que la acción está en marcha.
- Que recibirá el resultado cuando corresponda.

La misión de Nova-2 no es conversar.

La misión de Nova-2 es transmitir confianza operativa.
