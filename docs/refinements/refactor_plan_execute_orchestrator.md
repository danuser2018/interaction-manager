# Refinamiento de Feature: Migración al Modelo Resolve -> Execute Plan

**Documento de origen:** [refactor_plan_execute_orchestrator.md](file:///home/danuser2018/workspace/interaction-manager/docs/features/refactor_plan_execute_orchestrator.md)

---

## 1. Resumen y Contexto de Negocio

El motor del orquestador (`orchestrator`) ha sido refactorizado recientemente (según las directrices de diseño del [ADR-014](file:///home/danuser2018/workspace/home-assistant/docs/adr/adr-014-refactorizacion-orquestador.md)) para dividir su flujo monolítico en dos etapas independientes:
1. **Resolución de Intención (`IntentResolver`)**: Analiza la orden en lenguaje natural del usuario y devuelve un plan de ejecución estructurado (`ExecutionPlan`).
2. **Ejecución de Plugins (`PluginExecutor`)**: Toma un plan de ejecución y ejecuta de manera secuencial los plugins configurados.

El microservicio `interaction-manager` continúa consumiendo el endpoint legado monolítico `/api/v1/execute`. Esta acoplación impide realizar análisis, validaciones de seguridad o inyecciones de parámetros entre la fase de resolución y la de ejecución.

El objetivo de esta feature es refactorizar el `interaction-manager` para que consuma de forma explícita los nuevos endpoints desacoplados `/api/v1/resolve` y `/api/v1/execute-plan`. Este cambio es una refactorización interna y no debe alterar en absoluto el comportamiento funcional percibido por el usuario final, pero es fundamental para la evolución del pipeline de NOVA-2.

---

## 2. Análisis de Servicios e Impacto

| Servicio | Impacto | Descripción del Cambio |
| :--- | :--- | :--- |
| `interaction-manager` | Modificar | 1. Modificar `app/clients/orchestrator_client.py` eliminando la función `execute_interaction` e implementando las funciones `resolve_intent` y `execute_plan`. <br>2. Modificar `app/services/interaction_pipeline.py` para invocar en secuencia `/resolve` y luego `/execute-plan`, incluyendo la medición de tiempos e impresión de logs detallados. <br>3. Modificar `tests/test_clients.py` y `tests/test_pipeline.py` para adaptar los mocks y aserciones unitarias. |
| `orchestrator` | Ninguno | Sin impacto. Los endpoints ya están disponibles y testeados desde su propia refactorización. |

### Justificación de necesidad de ADR
No se requiere un nuevo ADR para este cambio, puesto que la decisión de red, la división arquitectónica en dos etapas y los nuevos contratos de comunicación ya están justificados y documentados formalmente en el [ADR-014](file:///home/danuser2018/workspace/home-assistant/docs/adr/adr-014-refactorizacion-orquestador.md). Esta refactorización es la ejecución de dicha decisión en el cliente correspondiente.

---

## 3. Especificación de Comportamiento (Criterios de Aceptación)

### Escenario 1: Ejecución exitosa de la interacción con el flujo desacoplado (Resolve -> Execute Plan)
```gherkin
Dado que el usuario dice "hola mundo"
Y el pipeline de interacción recibe el archivo de audio correspondiente
Cuando el pipeline invoca el endpoint de resolución /api/v1/resolve con la transcripción
Entonces el Orchestrator debe retornar un objeto ExecutionPlan válido
Y el pipeline debe invocar el endpoint de ejecución /api/v1/execute-plan enviando dicho ExecutionPlan
Y el Orchestrator debe responder con un AssistantResponse que indique éxito y contenga la respuesta de voz
Y el Interaction Manager debe continuar con la síntesis TTS y reproducción de la respuesta de voz con éxito.
```

### Escenario 2: Error de red durante Resolve
```gherkin
Dado que el pipeline de interacción intenta invocar /api/v1/resolve para una transcripción
Cuando ocurre un error de conexión HTTP o de tiempo de espera (timeout) al contactar con el Orchestrator
Entonces el cliente del Interaction Manager debe lanzar una excepción de tipo OrchestratorUnavailableError
Y el pipeline debe detenerse de inmediato sin intentar invocar /api/v1/execute-plan
Y el manejador de errores debe procesar la excepción devolviendo el audio de emergencia correspondiente a servicio no disponible.
```

### Escenario 3: Respuesta fallida de la API en Resolve (e.g. ValidationError)
```gherkin
Dado que el pipeline de interacción envía una solicitud vacía o malformada a /api/v1/resolve
Cuando el Orchestrator responde con un código de estado HTTP 422 (ValidationError)
Entonces el cliente del Interaction Manager debe capturar la respuesta y elevar una excepción de tipo OrchestratorResponseError
Y el pipeline debe detenerse sin llamar a /api/v1/execute-plan.
```

### Escenario 4: Error de red durante la ejecución del plan
```gherkin
Dado que el pipeline obtuvo un ExecutionPlan válido tras llamar a /api/v1/resolve
Cuando el pipeline intenta enviar el plan a /api/v1/execute-plan y ocurre un fallo de red o timeout
Entonces el cliente del Interaction Manager debe lanzar una excepción de tipo OrchestratorUnavailableError
Y la interacción debe finalizar llamando al manejador de errores para reproducir el audio de contingencia.
```

### Escenario 5: Error de lógica interna en Execute Plan (respuesta con success=False)
```gherkin
Dado que el pipeline obtuvo un ExecutionPlan válido tras llamar a /api/v1/resolve
Y el pipeline envía el plan a /api/v1/execute-plan
Cuando el Orchestrator responde con un código HTTP 200 pero el campo success en el payload de AssistantResponse es false
Entonces el cliente del Interaction Manager debe registrar el mensaje recibido y lanzar una excepción de tipo OrchestratorResponseError
Y la interacción debe finalizar procesando el error para reproducir el audio de contingencia correspondiente.
```

### Escenario 6: Registro de logs y medición de tiempos en el pipeline exitoso
```gherkin
Dado que el pipeline de interacción ejecuta con éxito el flujo Resolve -> Execute Plan
Cuando finaliza la llamada al orquestador
Entonces el sistema debe registrar en los logs de manera secuencial los siguientes mensajes informativos (en inglés):
- "Resolving user intent..."
- "ExecutionPlan received."
- "Executing plan..."
- "Assistant response received."
Y registrar los logs de tiempos en formato decimal indicando segundos (s) para la resolución, ejecución y el tiempo total.
```

---

## 4. Diseño Técnico y Contratos

### Métodos del Cliente HTTP (`app/clients/orchestrator_client.py`)

Se reemplazará `execute_interaction` por dos nuevos métodos:

```python
async def resolve_intent(text: str) -> dict:
    """
    Sends the user query text to the Orchestrator resolve endpoint.
    POST /api/v1/resolve
    Request payload: {"text": text}
    Returns: ExecutionPlan JSON structure (dict)
    Raises:
        OrchestratorUnavailableError: If connection/timeout issues occur.
        OrchestratorResponseError: If server responds with HTTP errors (e.g. 422).
    """
```

```python
async def execute_plan(plan: dict) -> str:
    """
    Sends the ExecutionPlan JSON structure to the Orchestrator execute-plan endpoint.
    POST /api/v1/execute-plan
    Request payload: plan (ExecutionPlan schema)
    Returns: The response speech string.
    Raises:
        OrchestratorUnavailableError: If connection/timeout issues occur.
        OrchestratorResponseError: If server responds with HTTP errors (e.g. 400, 422)
                                   or if the returned 'success' field is False.
    """
```

> [!NOTE]
> **Gestión de Excepciones del Cliente HTTP (D-01):** 
> Los fallos de red y conexión (tales como `httpx.RequestError`, `httpx.ConnectError` o `httpx.TimeoutException`) deben ser capturados y relanzados como `OrchestratorUnavailableError`.
> Por el contrario, los errores de respuesta HTTP devueltos por el servidor (capturados mediante `httpx.HTTPStatusError` tras lanzar `response.raise_for_status()`, como por ejemplo 400 o 422), deben ser elevados como `OrchestratorResponseError`.

### Modelos y Contratos de Datos (English Schema Reference)

#### 1. UserRequest (Payload para `/resolve`)
```json
{
  "text": "string"
}
```

#### 2. ExecutionPlan (Payload para `/execute-plan` y retorno de `/resolve`)
```json
{
  "steps": [
    {
      "plugin": "string",
      "confidence": "number (optional)",
      "parameters": "object (optional)",
      "channel": "string (optional)",
      "context": {
        "raw_text": "string",
        "normalized_text": "string",
        "metadata": "object (optional)"
      },
      "security": "object (optional)"
    }
  ]
}
```

#### 3. AssistantResponse (Retorno de `/execute-plan`)
```json
{
  "success": "boolean",
  "plugin_used": "string",
  "speech": "string",
  "execution_time_ms": "integer"
}
```

### Cambios en el Pipeline (`app/services/interaction_pipeline.py`)

La función `process_interaction` se modificará para secuenciar ambas llamadas, instrumentando logs y midiendo tiempos con `time.perf_counter()`:

```python
    # 2. Orchestrator
    logger.info("Resolving user intent...")
    resolve_start = time.perf_counter()
    plan = await orchestrator_client.resolve_intent(transcription)
    resolve_time = time.perf_counter() - resolve_start
    logger.info("ExecutionPlan received.")
    
    logger.info("Executing plan...")
    execute_start = time.perf_counter()
    response_text = await orchestrator_client.execute_plan(plan)
    execute_time = time.perf_counter() - execute_start
    logger.info("Assistant response received.")
    
    total_time = resolve_time + execute_time
    logger.info(f"Resolution time: {resolve_time:.4f}s")
    logger.info(f"Execution time: {execute_time:.4f}s")
    logger.info(f"Total time: {total_time:.4f}s")
    
    if not response_text:
        raise OrchestratorResponseError("Orchestrator returned an empty response.")
```

---

## 5. Casos de Borde y Manejo de Errores

| Caso de Borde | Comportamiento Esperado |
| :--- | :--- |
| **Timeout en la conexión a `/resolve`** | La llamada a `/resolve` superará el tiempo límite, elevando un `OrchestratorUnavailableError`. El pipeline se interrumpe de inmediato y el error es manejado por `error_handler`. |
| **Timeout en la conexión a `/execute-plan`** | Se elevará un `OrchestratorUnavailableError`. La interacción finaliza ejecutando el flujo de contingencia del error handler. |
| **`success=False` retornado por `/execute-plan`** | El cliente lanzará `OrchestratorResponseError` de forma que el comportamiento observado de fallback sea idéntico al comportamiento legado. |
| **Orchestrator devuelve HTTP 400 (PluginNotFoundError)** | Capturado como `httpx.HTTPStatusError`, elevando `OrchestratorResponseError`. El pipeline finaliza con error. |
| **Orchestrator devuelve HTTP 422 (ValidationError)** | Ocurre ante esquemas corruptos en cualquiera de las fases. Es capturado por el cliente como `HTTPStatusError` y elevado como `OrchestratorResponseError`. |

---

## 6. Estrategia de Testing

- **Pruebas Unitarias de Clientes (`tests/test_clients.py`)**:
  - Eliminar los tests de `execute_interaction`.
  - Crear `test_resolve_intent_success` verificando la llamada correcta a `/resolve` y retorno del diccionario.
  - Crear `test_resolve_intent_failure` verificando que fallos de conexión/red (como `httpx.ConnectError`) eleven `OrchestratorUnavailableError`.
  - Crear `test_resolve_intent_http_error` verificando que respuestas HTTP con código de error (como 422) eleven `OrchestratorResponseError`.
  - Crear `test_execute_plan_success` verificando el envío correcto del diccionario plan a `/execute-plan` y el retorno del `speech`.
  - Crear `test_execute_plan_unsuccessful` verificando que un response con `success=False` eleve `OrchestratorResponseError`.
  - Crear `test_execute_plan_failure` verificando que fallos de red eleven `OrchestratorUnavailableError`.
  - Crear `test_execute_plan_http_error` verificando que respuestas HTTP con código de error (como 400 o 422) eleven `OrchestratorResponseError`.

- **Pruebas Unitarias de Pipeline (`tests/test_pipeline.py`)**:
  - Actualizar `test_process_interaction_success` mockeando `resolve_intent` y `execute_plan`.
  - Actualizar `test_process_interaction_orchestrator_failure` para simular que `resolve_intent` o `execute_plan` fallan y elevan `OrchestratorResponseError`.
  - Comprobar que los logs registran los eventos de resolución y ejecución, así como las mediciones de tiempos de resolución, ejecución y total en segundos.

---

## 7. Plan de Implementación

- [ ] **Tarea 1 (Código):** Modificar `app/clients/orchestrator_client.py` implementando `resolve_intent` y `execute_plan`, y eliminando `execute_interaction`.
- [ ] **Tarea 2 (Código):** Modificar `app/services/interaction_pipeline.py` para invocar en secuencia `resolve_intent` y `execute_plan` de `orchestrator_client`, registrando los tiempos de resolución, ejecución y el total.
- [ ] **Tarea 3 (Tests):** Modificar `tests/test_clients.py` eliminando las pruebas de `execute_interaction` e implementando los casos correspondientes a `resolve_intent` y `execute_plan`.
- [ ] **Tarea 4 (Tests):** Modificar `tests/test_pipeline.py` adaptando los mocks de `orchestrator_client` al nuevo flujo desacoplado.
- [ ] **Tarea 5 (Verificación):** Ejecutar `venv/bin/pytest` localmente para garantizar que todos los tests pasen con éxito.
- [ ] **Tarea 6 (Documentación):** Registrar los cambios realizados en el archivo `CHANGELOG.md` en la sección `[Sin publicar]` en castellano.
