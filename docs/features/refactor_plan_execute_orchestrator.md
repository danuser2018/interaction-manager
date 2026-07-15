# Especificación de Refactorización
# Migración de Interaction Manager al modelo Resolve → Execute Plan

**Estado:** Propuesto

**Tipo:** Refactorización interna

**Impacto:** Interaction Manager, Orchestrator

---

# 1. Introducción

Tras la refactorización del Orchestrator, éste dispone de tres endpoints:

- `POST /api/v1/resolve`
- `POST /api/v1/execute-plan`
- `POST /api/v1/execute` (compatibilidad)

Actualmente, `Interaction Manager` continúa utilizando el endpoint legado `POST /api/v1/execute`, por lo que todavía no aprovecha la separación entre resolución de intención y ejecución.

Esta refactorización tiene como objetivo adaptar Interaction Manager al nuevo modelo de planificación, permitiendo eliminar posteriormente el endpoint legado.

---

# 2. Objetivos

## Objetivos

- Consumir explícitamente el endpoint de resolución.
- Consumir explícitamente el endpoint de ejecución.
- Mantener exactamente el comportamiento funcional actual.
- Eliminar el acoplamiento con el endpoint legado.
- Preparar Interaction Manager para futuras etapas del pipeline.

## Objetivos no incluidos

- No modificar la lógica del Intent Resolver.
- No modificar Plugin Executor.
- No introducir parámetros.
- No introducir canales.
- No introducir Security Manager.
- No introducir Context Service.

---

# 3. Situación actual

Actualmente Interaction Manager realiza una única llamada.

```text
Interaction Manager
        │
        ▼
POST /execute
        │
        ▼
Orchestrator
        │
        ▼
Respuesta
```

Toda la lógica de planificación permanece oculta.

---

# 4. Arquitectura objetivo

Tras esta refactorización el flujo será:

```text
Interaction Manager
        │
        │
        ├──────────────► POST /resolve
        │                    │
        │                    ▼
        │              ExecutionPlan
        │
        └──────────────► POST /execute-plan
                             │
                             ▼
                       AssistantResponse
```

Interaction Manager pasa a ser el coordinador explícito de ambas fases.

---

# 5. Flujo de ejecución

## Paso 1

Interaction Manager envía el texto reconocido al endpoint:

```
POST /api/v1/resolve
```

Obtiene un ExecutionPlan.

---

## Paso 2

Interaction Manager envía el ExecutionPlan al endpoint:

```
POST /api/v1/execute-plan
```

Obtiene la respuesta del asistente.

---

## Paso 3

Interaction Manager continúa exactamente igual que actualmente:

- genera el audio
- reproduce la respuesta
- finaliza la interacción

---

# 6. Cambios funcionales

No existen cambios funcionales visibles para el usuario.

El usuario deberá obtener exactamente las mismas respuestas.

La única diferencia es la secuencia de llamadas entre servicios.

---

# 7. Contratos API

## Resolve

Request

```json
{
  "text": "qué tiempo hace hoy"
}
```

Response

```json
{
  "steps": [
    {
      "plugin": "WeatherPlugin"
    }
  ]
}
```

---

## Execute Plan

Request

```json
{
  "steps": [
    {
      "plugin": "WeatherPlugin"
    }
  ]
}
```

Response

```json
{
  "success": true,
  "speech": "Actualmente hace 28 grados."
}
```

---

# 8. Manejo de errores

Interaction Manager deberá tratar de forma independiente los errores de cada fase.

## Error durante Resolve

No deberá intentarse ejecutar ningún plan.

La interacción finalizará devolviendo el error correspondiente.

---

## Error durante Execute Plan

La interacción finalizará con la respuesta de error generada por el Executor.

---

## Timeout

Cada llamada mantendrá sus propios timeouts.

Los errores deberán registrarse indicando la fase en la que se producen.

---

# 9. Logging

Interaction Manager deberá registrar:

Inicio de resolución

```text
Resolving user intent...
```

Plan recibido

```text
ExecutionPlan received.
```

Inicio de ejecución

```text
Executing plan...
```

Respuesta recibida

```text
Assistant response received.
```

Tiempo de resolución

Tiempo de ejecución

Tiempo total

---

# 10. Compatibilidad

Durante esta fase deberán coexistir los tres endpoints del Orchestrator.

```
POST /resolve
```

```
POST /execute-plan
```

```
POST /execute
```

El endpoint legado permanecerá disponible hasta completar la migración del resto de consumidores.

---

# 11. Plan de migración

## Paso 1

Actualizar el cliente HTTP del Interaction Manager.

---

## Paso 2

Implementar la llamada a `/resolve`.

---

## Paso 3

Consumir el ExecutionPlan recibido.

---

## Paso 4

Invocar `/execute-plan`.

---

## Paso 5

Actualizar las pruebas unitarias.

---

## Paso 6

Actualizar pruebas de integración.

---

## Paso 7

Actualizar documentación.

---

# 12. Requisitos funcionales

## RF-001

Interaction Manager deberá utilizar el endpoint `/api/v1/resolve`.

---

## RF-002

Interaction Manager deberá consumir el objeto `ExecutionPlan`.

---

## RF-003

Interaction Manager deberá invocar `/api/v1/execute-plan`.

---

## RF-004

El comportamiento observable deberá permanecer idéntico.

---

## RF-005

La secuencia de llamadas deberá ser:

```
Resolve

↓

Execute Plan
```

---

## RF-006

Interaction Manager no deberá construir ni modificar el ExecutionPlan recibido.

Deberá actuar únicamente como coordinador.

---

# 13. Requisitos no funcionales

## RNF-001

La latencia añadida deberá ser despreciable.

---

## RNF-002

La implementación deberá mantener compatibilidad completa con la API actual del Interaction Manager.

---

## RNF-003

La lógica de negocio continuará residiendo exclusivamente en el Orchestrator.

---

## RNF-004

Interaction Manager no deberá interpretar el contenido del ExecutionPlan.

---

## RNF-005

La migración deberá permitir eliminar posteriormente el endpoint:

```
POST /api/v1/execute
```

sin introducir cambios adicionales en Interaction Manager.

---

# 14. Criterios de aceptación

Se considerará completada la refactorización cuando:

- Interaction Manager no invoque nunca `POST /execute`.
- Todas las llamadas se realicen mediante `POST /resolve` y `POST /execute-plan`.
- Todas las pruebas existentes continúen pasando.
- El comportamiento observado por el usuario sea idéntico.
- La documentación del sistema refleje el nuevo flujo.

---

# 15. Trabajo futuro

Una vez completada esta migración será posible:

- Eliminar el endpoint legado `/execute`.
- Introducir un Parameter Resolver.
- Incorporar un Security Manager entre planificación y ejecución.
- Incorporar un Context Service.
- Introducir validadores del ExecutionPlan.
- Añadir optimizadores o transformadores del plan antes de su ejecución.

Esta refactorización constituye el último paso para completar la transición del modelo de ejecución monolítico al modelo basado en planificación, consolidando el `ExecutionPlan` como el contrato interno de ejecución de NOVA-2.