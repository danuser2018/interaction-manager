# Interaction Manager

Microservicio encargado de coordinar el flujo completo de interacción de un asistente de voz local.

## Descripción

Interaction Manager es el componente responsable de conectar los distintos servicios del ecosistema:

* Speech-to-Text (STT)
* Orchestrator
* Text-to-Speech (TTS)

Su responsabilidad consiste en detectar nuevas entradas de audio, convertirlas a texto, obtener una respuesta del Orchestrator, sintetizar dicha respuesta mediante TTS y dejar el resultado disponible para su reproducción.

El servicio está diseñado para ejecutarse como un proceso de larga duración dentro de un contenedor Docker y formar parte de una arquitectura modular basada en microservicios.

## Objetivos

* Detectar nuevos archivos de audio en una carpeta de entrada.
* Gestionar el ciclo completo STT → Orchestrator → TTS.
* Depositar los audios generados en una carpeta de salida.
* Mantener una responsabilidad única y bien definida.
* Permitir despliegues independientes mediante Docker.
* Facilitar la integración con otros componentes mediante volúmenes compartidos.
* Mantener una arquitectura simple, desacoplada y fácilmente extensible.

## Fuera de alcance

Este servicio NO es responsable de:

* Captura de audio.
* Gestión de micrófonos.
* Voice Activity Detection (VAD).
* Conversión Speech-to-Text.
* Síntesis Text-to-Speech.
* Selección de plugins.
* Gestión de memoria.
* Ejecución de LLMs.
* Reproducción de audio.
* Gestión de altavoces.
* Gestión de contexto conversacional.

## Arquitectura

Interaction Manager forma parte de una arquitectura más amplia:

```text
                 +----------------+
                 | Mic Daemon     |
                 +--------+-------+
                          |
                          |
                          ▼
                    /data/input
                          |
                          ▼
                 +----------------+
                 | Interaction    |
                 | Manager        |
                 +--------+-------+
                          |
          +---------------+---------------+
          |                               |
          ▼                               ▼
   +-------------+                 +-------------+
   | STT Service |                 | Orchestrator|
   +-------------+                 +-------------+
                                           |
                                           ▼
                                    +-------------+
                                    | TTS Service |
                                    +-------------+
                                           |
                                           ▼
                                     /data/output
                                           |
                                           ▼
                                  +----------------+
                                  | Speaker        |
                                  | Watchdog       |
                                  +----------------+
```

## Flujo de procesamiento

El ciclo de vida de una petición sigue los siguientes pasos:

```text
1. Nuevo archivo WAV aparece en /data/input

2. El archivo se mueve a /data/processing

3. Se envía al servicio STT

4. Se obtiene la transcripción

5. Se envía el texto al Orchestrator

6. Se obtiene la respuesta textual

7. Se envía la respuesta al servicio TTS

8. Se recibe un WAV generado

9. Se almacena en /data/output

10. Se elimina el archivo de /data/processing
```

## Gestión de estados mediante carpetas

El servicio utiliza una máquina de estados sencilla basada en directorios:

```text
/data
├── input/
├── processing/
├── output/
└── error/
```

### input

Contiene archivos pendientes de procesar.

### processing

Contiene archivos actualmente en procesamiento.

### output

Contiene respuestas sintetizadas listas para ser consumidas por otros componentes.

### error

Contiene archivos cuyo procesamiento ha fallado.

## Gestión de errores

Si ocurre un error en cualquiera de las etapas:

* STT
* Orchestrator
* TTS

el archivo original será movido a:

```text
/data/error
```

Esto permite su análisis posterior y evita la pérdida de peticiones.

## Principios de diseño

Este proyecto sigue los siguientes principios:

* Single Responsibility Principle (SRP).
* Docker First.
* Worker First.
* Stateless Processing.
* Configuración mediante variables de entorno.
* Componentes fácilmente testeables.
* Separación clara de responsabilidades.
* Infraestructura desacoplada.
* Bajo consumo de recursos.
* Extensibilidad mediante adaptadores futuros.

## Tecnologías utilizadas

* Python 3.12
* HTTPX
* Watchdog
* Docker
* Docker Compose
* Pytest

## Interfaces consumidas

### STT Service

Endpoint utilizado:

```http
POST /v1/transcriptions
```

Respuesta esperada:

```json
{
  "text": "qué tiempo hace hoy"
}
```

### Orchestrator

Endpoint utilizado:

```http
POST /api/v1/execute
```

Petición:

```json
{
  "text": "qué tiempo hace hoy"
}
```

Respuesta esperada:

```json
{
  "success": true,
  "speech": "Actualmente hace 22 grados"
}
```

### TTS Service

Endpoint utilizado:

```http
POST /synthesize
```

Petición:

```json
{
  "msg": "Actualmente hace 22 grados"
}
```

Respuesta esperada:

```text
audio/wav
```

## Configuración

Toda la configuración se realiza mediante variables de entorno.

| Variable              | Obligatoria | Descripción               |
| --------------------- | ----------- | ------------------------- |
| STT_BASE_URL          | Sí          | URL base del servicio STT |
| ORCHESTRATOR_BASE_URL | Sí          | URL base del Orchestrator |
| TTS_BASE_URL          | Sí          | URL base del servicio TTS |
| INPUT_DIR             | No          | Carpeta de entrada        |
| PROCESSING_DIR        | No          | Carpeta de procesamiento  |
| OUTPUT_DIR            | No          | Carpeta de salida         |
| ERROR_DIR             | No          | Carpeta de errores        |
| POLL_INTERVAL_SECONDS | No          | Intervalo de sondeo       |
| DEFAULT_LANGUAGE      | No          | Idioma enviado al STT     |
| LOG_LEVEL             | No          | Nivel de logging          |

Valores por defecto:

```env
INPUT_DIR=/data/input
PROCESSING_DIR=/data/processing
OUTPUT_DIR=/data/output
ERROR_DIR=/data/error

POLL_INTERVAL_SECONDS=1
DEFAULT_LANGUAGE=auto
LOG_LEVEL=INFO
```

## Requisitos previos

Es necesario disponer de:

* Docker
* Docker Compose

No es necesario instalar Python localmente.

## Instalación

### Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd interaction-manager
```

### Construir la imagen Docker

```bash
docker build -t interaction-manager .
```

### Ejecutar el contenedor

```bash
docker run -d \
  --name interaction-manager \
  -v $(pwd)/data:/data \
  -e STT_BASE_URL=http://stt:8000 \
  -e ORCHESTRATOR_BASE_URL=http://orchestrator:8000 \
  -e TTS_BASE_URL=http://tts:8000 \
  interaction-manager
```

## Instalación mediante Docker Compose

```yaml
version: "3.9"

services:

  interaction-manager:
    build: .
    container_name: interaction-manager

    environment:
      STT_BASE_URL: http://stt:8000
      ORCHESTRATOR_BASE_URL: http://orchestrator:8000
      TTS_BASE_URL: http://tts:8000

    volumes:
      - ./data:/data

    restart: unless-stopped

    depends_on:
      - stt
      - orchestrator
      - tts

  stt:
    image: stt-service

  orchestrator:
    image: voice-orchestrator

  tts:
    image: tts-capability
```

Arranque:

```bash
docker compose up -d
```

## Ejecución

Interaction Manager se ejecuta como un proceso de larga duración.

Durante su ejecución:

1. Vigila la carpeta configurada como INPUT_DIR.
2. Detecta nuevos archivos WAV.
3. Los mueve a PROCESSING_DIR.
4. Ejecuta el pipeline STT → Orchestrator → TTS.
5. Deposita el resultado en OUTPUT_DIR.
6. Elimina el archivo de PROCESSING_DIR.
7. En caso de error mueve el archivo a ERROR_DIR.

El proceso permanece en ejecución hasta recibir una señal de parada del sistema operativo.

## Estructura esperada del proyecto

```text
interaction-manager/
├── app/
│   ├── clients/
│   │   ├── stt_client.py
│   │   ├── orchestrator_client.py
│   │   └── tts_client.py
│   ├── services/
│   │   ├── file_watcher.py
│   │   └── interaction_pipeline.py
│   ├── config/
│   │   └── settings.py
│   ├── models/
│   └── main.py
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── CONTRIBUTING.md
└── CHANGELOG.md
```

## Logging

Debe utilizarse el módulo estándar `logging`.

Debe registrarse:

* Inicio de la aplicación.
* Detección de nuevos archivos.
* Inicio y fin de procesamiento.
* Llamadas a servicios externos.
* Tiempos de procesamiento.
* Errores.

No debe registrarse:

* Audio del usuario.
* Datos sensibles.
* Información privada.

## Testing

El proyecto debe incluir:

### Tests unitarios

Para:

* Watcher de archivos.
* Clientes HTTP.
* Gestión de configuración.
* Pipeline de procesamiento.

### Tests de integración

Para:

* Flujo completo STT → Orchestrator → TTS.
* Gestión de errores.
* Gestión de carpetas.

La ejecución de tests debe realizarse mediante:

```bash
pytest
```

## Desarrollo local

Ejecutar la aplicación:

```bash
python -m app.main
```

Ejecutar tests:

```bash
pytest
```

## Evolución futura

Posibles extensiones futuras:

* Soporte para Telegram.
* Soporte para MQTT.
* Soporte para HTTP.
* Soporte para WebSockets.
* Procesamiento concurrente.
* Colas de mensajes.
* Métricas Prometheus.
* Health checks.
* Trazabilidad distribuida.

Estas funcionalidades quedan explícitamente fuera del alcance del MVP.

## Contribuciones

Antes de realizar cualquier contribución es obligatorio consultar:

```text
CONTRIBUTING.md
```

Este documento define:

* Convenciones de código.
* Arquitectura.
* Estándares de calidad.
* Estrategia de testing.
* Flujo de ramas.
* Revisión de cambios.
* Buenas prácticas de desarrollo.

Todo cambio deberá cumplir dichas directrices.

## Licencia

Pendiente de definir por el propietario del repositorio.
