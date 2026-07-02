# Definición Funcional

## Simplificación del mecanismo de audio de emergencia del Interaction Manager

### Objetivo

Simplificar el mecanismo de respuesta de emergencia del Interaction Manager cuando no es posible sintetizar voz mediante el servicio TTS.

Actualmente el sistema mantiene un conjunto de audios pregrabados específicos para distintos tipos de error. Este cambio sustituye dicho comportamiento por un único audio de emergencia reutilizable para cualquier fallo en el que el TTS no pueda generar la respuesta correspondiente.

El objetivo es reducir la complejidad del sistema, disminuir el mantenimiento de recursos de audio y desacoplar los mensajes de emergencia de la naturaleza concreta del error.

---

# Requisitos funcionales

## RF-1. Respuesta garantizada

El Interaction Manager continuará garantizando que toda interacción finaliza con una respuesta hacia el usuario.

Cuando la respuesta no pueda sintetizarse mediante TTS, deberá utilizarse un audio de emergencia.

---

## RF-2. Audio de emergencia único

El sistema dispondrá de un único archivo de audio de emergencia.

Este archivo sustituirá a todos los audios específicos actualmente existentes en el directorio de emergencias.

---

## RF-3. Política de utilización

Siempre que el Interaction Manager no pueda obtener un audio válido desde el servicio TTS, reproducirá el audio de emergencia único.

La decisión será independiente de:

* la fase del flujo donde se haya producido el error;
* el tipo de excepción;
* el servicio que haya originado el fallo;
* el mensaje de error generado internamente.

---

## RF-4. Independencia de la causa del error

El audio de emergencia no deberá transmitir información específica sobre el origen del problema.

Su única finalidad será informar al usuario de que la operación no ha podido completarse.

---

## RF-5. Conservación del tratamiento interno de errores

La simplificación únicamente afecta a la comunicación hacia el usuario.

El Interaction Manager continuará:

* detectando los distintos tipos de error;
* clasificándolos internamente;
* registrándolos mediante logging;
* devolviendo el resultado interno correspondiente para facilitar diagnóstico y observabilidad.

---

## RF-6. Compatibilidad del flujo

No se modifica el flujo conversacional existente:

1. recepción del audio;
2. STT;
3. Orchestrator;
4. TTS;
5. reproducción mediante Speaker Watchdog.

Únicamente cambia la política aplicada cuando el paso de TTS no produce un audio reproducible.

---

# Requisitos no funcionales

## RNF-1. Reducción de complejidad

El sistema deberá minimizar el número de recursos de audio de emergencia mantenidos.

El mantenimiento futuro deberá requerir un único archivo de respaldo.

---

## RNF-2. Desacoplamiento

Los recursos de audio de emergencia no deberán depender de la taxonomía interna de errores del sistema.

La incorporación de nuevos tipos de error no requerirá crear nuevos audios.

---

## RNF-3. Mantenibilidad

La incorporación de nuevas casuísticas de error en cualquier componente del flujo no implicará modificaciones en el mecanismo de audio de emergencia.

---

## RNF-4. Robustez

Ante cualquier fallo que impida generar audio mediante TTS, el sistema deberá seguir proporcionando una respuesta audible utilizando el archivo de emergencia.

---

## RNF-5. Consistencia

Todos los escenarios de fallo del TTS producirán el mismo comportamiento observable para el usuario.

---

# Criterios de aceptación

* Existe un único archivo de audio de emergencia.
* Los audios específicos anteriores dejan de utilizarse.
* Cualquier fallo en la generación del audio mediante TTS provoca la reproducción del audio de emergencia único.
* El logging interno continúa diferenciando las distintas causas del error.
* La incorporación de un nuevo tipo de error no requiere crear nuevos recursos de audio.
* El comportamiento del usuario es consistente independientemente de la causa que impidió generar el audio mediante TTS.
