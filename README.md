# Toka – User Management System

Sistema de gestión de usuarios basado en microservicios con autenticación OAuth2/JWT, auditoría de eventos, y agente de IA con RAG.

## Arquitectura

```
Frontend (React) → API Gateway → Auth Service  → PostgreSQL + Redis
                                → User Service  → PostgreSQL
                                → Audit Service → MongoDB + RabbitMQ
                                → AI Agent      → Qdrant + Lemma → OpenAI
```

## Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Backend | Python FastAPI (async, Clean Architecture + DDD) |
| Frontend | React 18 + TypeScript + Vite + Zustand |
| Auth | JWT (RS256/HS256) con refresh tokens |
| Audit | Event-driven con RabbitMQ + MongoDB |
| AI Agent | LangChain + RAG (Qdrant) + Lemma AI Gateway |
| AI Gateway | [@nxuss/lemma](https://www.npmjs.com/package/@nxuss/lemma) (cache semántico, privacy firewall, cost router) |
| Testing | pytest (backend), Vitest + RTL (frontend) |
| Infra | Docker Compose (12 servicios) |

## Microservicios

| Servicio | Puerto | DB | Descripción |
|---|---|---|---|
| `auth-service` | 8001 | PostgreSQL + Redis | Registro, login, JWT, refresh tokens |
| `user-service` | 8002 | PostgreSQL | CRUD usuarios, roles, permisos |
| `audit-service` | 8003 | MongoDB | Logs de auditoría (event-driven) |
| `ai-agent-service` | 8004 | Qdrant | RAG + queries con OpenAI vía Lemma |
| `api-gateway` | 8000 | — | Proxy reverso a todos los servicios |
| `frontend` | 3000 | — | React SPA |

## Requisitos

- Docker & Docker Compose v2
- Node.js 20+ (solo para Lemma local)
- OpenAI API Key (para AI Agent)

## Inicio Rápido

```bash
# 1. Clonar y entrar
git clone <repo> && cd toka

# 2. Configurar variables (editar .env con tu OPENAI_API_KEY)
cp .env.example .env

# 3. Setup automático (instala Lemma + levanta Docker)
./setup.sh

# 4. Ver logs
docker compose logs -f
```

## Entorno Local (Manual)

```bash
# Variables de entorno
export OPENAI_API_KEY=sk-...

# Iniciar toda la infraestructura
docker compose up -d

# Ver estado
docker compose ps

# Logs de un servicio específico
docker compose logs -f auth-service
```

## Acceso a Servicios

| URL | Descripción |
|---|---|
| http://localhost:3000 | Frontend |
| http://localhost:8000 | API Gateway |
| http://localhost:8001/docs | Auth API (Swagger) |
| http://localhost:8002/docs | User API (Swagger) |
| http://localhost:8003/docs | Audit API (Swagger) |
| http://localhost:8004/docs | AI Agent API (Swagger) |
| http://localhost:8082 | Lemma Dashboard |
| http://localhost:15672 | RabbitMQ Management |

## Pruebas

```bash
# Tests de backend (cada servicio) con reporte de cobertura HTML
docker compose run --rm auth-service pytest --cov --cov-report=term --cov-report=html:coverage_html --cov-fail-under=70
docker compose run --rm user-service pytest --cov --cov-report=term --cov-report=html:coverage_html --cov-fail-under=70
docker compose run --rm audit-service pytest --cov --cov-report=term --cov-report=html:coverage_html --cov-fail-under=70
docker compose run --rm ai-agent-service pytest --cov --cov-report=term --cov-report=html:coverage_html --cov-fail-under=70

# Tests de frontend
cd frontend && npm test
```

| Servicio | Tests | Cobertura |
|---|---|---|
| auth-service | 66 ✅ | 89% |
| user-service | 97 ✅ | 87% |
| audit-service | 32 ✅ | 67% |
| ai-agent-service | 55 ✅ | 74% |
| frontend | 37 ✅ | — |

Los reportes HTML de cobertura se generan en `coverage/<service>/index.html`.

## API Endpoints

### Auth (`/api/v1/auth`)
- `POST /register` — Registro de usuario
- `POST /login` — Login (retorna JWT)
- `POST /refresh` — Refresh token
- `POST /logout` — Logout (invalida token)
- `GET /validate` — Validar token
- `GET /me` — Usuario actual

### Users (`/api/v1/users`)
- `GET /users` — Listar (paginado, filtrable)
- `GET /users/{id}` — Obtener usuario
- `PUT /users/{id}` — Actualizar
- `DELETE /users/{id}` — Eliminar usuario
- `POST /users/{id}/roles` — Asignar rol

### Roles (`/api/v1/roles`)
- `GET /roles` — Listar
- `POST /roles` — Crear
- `PUT /roles/{id}` — Actualizar
- `DELETE /roles/{id}` — Eliminar

### Audit (`/api/v1/audit`)
- `GET /audit/logs` — Listar logs (filtros)
- `GET /audit/logs/{id}` — Obtener log
- `GET /audit/stats` — Estadísticas

### AI Agent (`/api/v1/ai`)
- `POST /ai/query` — Consulta con RAG
- `POST /ai/report` — Generar reporte
- `POST /ai/ingest` — Ingestar documentos
- `GET /ai/evaluate` — Métricas de evaluación

## Documentación Adicional

- [Arquitectura y Diagrama Mermaid](docs/ARCHITECTURE.md)
- [DDD y Clean Architecture](docs/DDD_CLEAN_ARCHITECTURE.md)
- [Estrategia de Prompt Engineering](docs/PROMPT_ENGINEERING.md)
- [Diagnóstico de Incidentes](docs/DIAGNOSTIC.md)

## Estructura del Proyecto

```
toka/
├── docker-compose.yml       # Orquestación completa (12 servicios)
├── docker/                  # Dockerfiles base compartidos
├── services/
│   ├── auth-service/        # Autenticación (Dockerfile, .coveragerc)
│   ├── user-service/        # Usuarios y roles (Dockerfile, .coveragerc)
│   ├── audit-service/       # Auditoría (Dockerfile, .coveragerc)
│   ├── ai-agent-service/    # Agente IA (Dockerfile, .coveragerc)
│   └── api-gateway/         # Gateway (Dockerfile)
├── frontend/                # React SPA (Dockerfile.frontend)
├── coverage/                # Reportes HTML de cobertura
├── docs/                    # Documentación + diagrama PNG
├── scripts/                 # DB init scripts
├── .env                     # Variables de entorno (OPENAI_API_KEY)
├── .env.example             # Template de variables
└── setup.sh                 # Setup automatizado
```

## Clean Architecture (por Microservicio)

```
src/
├── domain/          # Entidades, Value Objects, Interfaces
├── application/     # Use Cases, DTOs
├── infrastructure/  # DB, MQ, Cache, APIs externas
└── api/             # FastAPI routes, middlewares, DI
```
