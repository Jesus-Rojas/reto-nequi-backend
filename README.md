# Nequi Chat API

API RESTful para procesamiento de mensajes de chat, construida con **FastAPI + SQLAlchemy + SQLite**.

## Stack

| Componente | Tecnología |
|---|---|
| Framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 |
| Base de datos | SQLite |
| Validación | Pydantic v2 |
| Pruebas | Pytest + HTTPX |
| Contenedor | Docker + Docker Compose |

---

## Arquitectura

```
app/
├── config.py                  # Configuración (pydantic-settings)
├── database.py                # Engine SQLAlchemy y sesión
├── main.py                    # Punto de entrada FastAPI
├── models/
│   └── message.py             # Modelo ORM Message
├── schemas/
│   └── message.py             # Schemas Pydantic (entrada/salida/error)
├── repositories/
│   └── message_repository.py  # Capa de acceso a datos
├── services/
│   ├── content_filter.py      # Filtro de contenido inapropiado
│   └── message_service.py     # Lógica de negocio
├── api/
│   ├── dependencies.py        # Inyección de dependencias FastAPI
│   ├── websocket_manager.py   # Gestor de conexiones WebSocket
│   └── routes/
│       └── messages.py        # Endpoints REST + WebSocket
└── core/
    ├── exceptions.py          # Excepciones de dominio
    ├── error_handlers.py      # Manejadores de error globales
    └── rate_limiter.py        # Middleware de limitación de tasa
```

Los principios SOLID se aplican de la siguiente manera:
- **S** — Cada clase tiene una única responsabilidad (repository, service, filter…)
- **O** — `ContentFilterService` acepta una lista de palabras inyectable
- **L** — Las dependencias se consumen por interfaz (tipo)
- **I** — Interfaces pequeñas y focalizadas
- **D** — Toda la lógica recibe sus dependencias por parámetro (DI vía FastAPI `Depends`)

---

## Inicio rápido con Docker Compose

```bash
# 1. Clonar el repositorio
git clone <url-del-repo> && cd reto-nequi

# 2. Crear archivo de entorno (opcional — los valores por defecto funcionan)
cp .env.example .env

# 3. Levantar el servicio
docker compose up --build

# La API queda disponible en http://localhost:8000
# Documentación interactiva: http://localhost:8000/docs
```

---

## Inicio sin Docker (desarrollo local)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

uvicorn app.main:app --reload
```

---

## Autenticación

Todos los endpoints REST requieren la cabecera `X-API-Key`.

```
X-API-Key: nequi-secret-key-change-in-production
```

Configura tu propia clave en `.env` → variable `API_KEY`.

---

## Documentación de la API

### POST `/api/messages`

Crea y procesa un nuevo mensaje.

**Cuerpo de la solicitud:**

```json
{
  "message_id": "msg-123456",
  "session_id": "session-abcdef",
  "content": "Hola, ¿cómo puedo ayudarte hoy?",
  "timestamp": "2024-01-15T14:30:00Z",
  "sender": "system"
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `message_id` | string | Identificador único del mensaje |
| `session_id` | string | Identificador de la sesión |
| `content` | string | Contenido (1–10 000 caracteres) |
| `timestamp` | ISO 8601 datetime | Marca de tiempo del mensaje |
| `sender` | `"user"` \| `"system"` | Remitente |

**Respuesta exitosa (201):**

```json
{
  "status": "success",
  "data": {
    "message_id": "msg-123456",
    "session_id": "session-abcdef",
    "content": "Hola, ¿cómo puedo ayudarte hoy?",
    "timestamp": "2024-01-15T14:30:00",
    "sender": "system",
    "metadata": {
      "word_count": 6,
      "character_count": 32,
      "processed_at": "2024-01-15T14:30:01",
      "is_filtered": false
    }
  }
}
```

**Códigos de error:**

| Código HTTP | `error.code` | Causa |
|---|---|---|
| 401 | `UNAUTHORIZED` | API key ausente o incorrecta |
| 409 | `DUPLICATE_MESSAGE` | Ya existe un mensaje con ese `message_id` |
| 422 | `VALIDATION_ERROR` | Campos faltantes o formato inválido |
| 429 | `RATE_LIMIT_EXCEEDED` | Demasiadas solicitudes por minuto |

---

### GET `/api/messages/{session_id}`

Recupera los mensajes de una sesión con paginación.

**Parámetros de consulta:**

| Parámetro | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `sender` | `user` \| `system` | — | Filtra por remitente |
| `limit` | int (1–100) | 20 | Máximo de resultados |
| `offset` | int (≥ 0) | 0 | Desplazamiento para paginación |

**Ejemplo:**

```
GET /api/messages/session-abcdef?sender=user&limit=10&offset=0
```

**Respuesta (200):**

```json
{
  "status": "success",
  "data": [...],
  "pagination": {
    "total": 42,
    "limit": 10,
    "offset": 0,
    "has_more": true
  }
}
```

---

### GET `/api/messages/search`

Busca mensajes por palabra clave en el contenido.

**Parámetros de consulta:**

| Parámetro | Requerido | Descripción |
|---|---|---|
| `keyword` | ✅ | Término de búsqueda (parcial, case-insensitive) |
| `session_id` | — | Restringe la búsqueda a una sesión |
| `limit` | — | (1–100, por defecto 20) |
| `offset` | — | (≥ 0, por defecto 0) |

---

### WebSocket `/ws/{session_id}`

Recibe notificaciones en tiempo real cuando se publica un nuevo mensaje en la sesión.

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/session-abcdef");
ws.onmessage = (event) => {
  const { event: type, data } = JSON.parse(event.data);
  console.log(type, data); // "new_message", { message_id, ... }
};
```

---

### GET `/health`

```json
{ "status": "ok", "version": "1.0.0" }
```

---

## Ejecución de pruebas

```bash
# Todas las pruebas con reporte de cobertura
pytest

# Solo pruebas unitarias
pytest tests/unit/

# Solo pruebas de integración
pytest tests/integration/

# Reporte HTML de cobertura
pytest --cov-report=html
```

La configuración exige un mínimo del **80 % de cobertura** (definido en `pytest.ini`).

---

## Variables de entorno

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/messages.db` | URL de conexión SQLAlchemy |
| `API_KEY` | `nequi-secret-key-change-in-production` | Clave de autenticación |
| `RATE_LIMIT_PER_MINUTE` | `60` | Solicitudes máximas por IP/minuto |
| `DEBUG` | `false` | Modo de depuración |


