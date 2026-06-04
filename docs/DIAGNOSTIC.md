# Ejercicio 4 – Diagnóstico: Incidente en Producción

## Escenario
"Los usuarios no pueden guardar registros, algunos microservicios responden con errores 500, y hay reportes de alta latencia en las respuestas de agentes de IA."

## Hipótesis Prioritarias (ordenadas por probabilidad/impacto)

| # | Hipótesis | Probabilidad | Impacto |
|---|---|---|---|
| 1 | **Conexión a base de datos agotada** (connection pool exhaustion en PostgreSQL) | Alta | Crítico |
| 2 | **RabbitMQ acumulando mensajes sin procesar** (consumer caído o lento) | Alta | Alto |
| 3 | **Rate limiting de OpenAI alcanzado** (429 Too Many Requests en AI Agent) | Media | Alto |
| 4 | **Cascading failure**: Auth Service lento → User Service timeout → Gateway 500 | Media | Crítico |
| 5 | **Redis fuera de servicio** (token blacklist no funciona → auth falla) | Baja | Crítico |
| 6 | **Problema de red entre contenedores** (DNS/resolución de nombres Docker) | Baja | Alto |

## Plan de Diagnóstico Sistemático

### Paso 1: Verificar Logs Centralizados (inmediato)

```bash
# Asumiendo Docker Compose con logging driver json-file
docker-compose logs --tail=100 --timestamps | grep -E "ERROR|CRITICAL|500|timeout|exception"
```

**Qué buscar:**
- Stack traces con `SQLAlchemy` o `connection pool` → Hipótesis 1
- `pika.exceptions.AMQPConnectionError` → Hipótesis 2
- `openai.RateLimitError` o `429` → Hipótesis 3
- `httpx.TimeoutException` en llamadas entre servicios → Hipótesis 4

### Paso 2: Health Check de Todos los Servicios

```bash
# Script rápido de health check
for svc in auth-service user-service audit-service ai-agent-service api-gateway; do
  status=$(curl -s -o /dev/null -w "%{http_code}" http://$svc:8000/health)
  echo "$svc: $status"
done
```

**Esperado**: Todos 200. Si alguno da 500 o timeout, ese es el foco.

### Paso 3: Verificar Conexiones a DB

```bash
# PostgreSQL: verificar conexiones activas
docker exec toka-postgres psql -U toka_user -c "SELECT count(*) FROM pg_stat_activity;"

# MongoDB: verificar status
docker exec toka-mongodb mongosh --quiet --eval "db.serverStatus().connections"

# Redis: verificar conectividad
docker exec toka-redis redis-cli -a toka_pass_2024 ping
```

### Paso 4: Verificar RabbitMQ

```bash
# Acceder a management UI o CLI
docker exec toka-rabbitmq rabbitmqctl list_queues name messages messages_ready messages_unacknowledged
```

**Qué buscar**: Queues con `messages` > 1000 y creciendo → consumer caído.

### Paso 5: Verificar Latencia de AI Agent

```bash
# Medir latencia de llamada a OpenAI a través de Lemma
curl -X POST http://localhost:8004/api/v1/ai/evaluate -H "Authorization: Bearer $TOKEN"

# Verificar rate limits en logs de Lemma
docker logs toka-lemma --tail=50 | grep -i "rate\|limit\|429"
```

## Uso de Logs Estructurados (JSON)

Cada servicio emite logs en formato JSON a stdout. Ejemplo:

```json
{
  "event": "login_attempt",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "ip_address": "192.168.1.100",
  "success": false,
  "reason": "invalid_password",
  "duration_ms": 45,
  "timestamp": "2026-06-04T10:30:00Z",
  "service": "auth-service",
  "level": "warn",
  "trace_id": "abc123"
}
```

### Pipeline de Diagnóstico con Logs

```bash
# 1. Buscar errores 500 en todos los servicios
docker-compose logs --since=10m | jq 'select(.level == "error" or .level == "critical")'

# 2. Identificar patrones de timeout entre servicios
docker-compose logs --since=30m | jq 'select(.duration_ms > 5000) | {service, event, duration_ms}'

# 3. Correlacionar trace_id para seguir request completo
docker-compose logs | jq 'select(.trace_id == "abc123") | {service, event, duration_ms, level}'
```

## Problemas Específicos de Agentes IA

### 1. Alta Latencia
- **Síntoma**: Queries AI toman >30s
- **Diagnóstico**: 
  ```bash
  docker-compose logs ai-agent-service | jq 'select(.event == "ai_query") | .latency_ms'
  ```
- **Causas probables**: 
  - Modelo muy grande (gpt-4o → cambiar a gpt-4o-mini para queries simples)
  - Contexto RAG muy grande (reducir top_k de 5 a 3)
  - Lemma cache frío (primeras queries siempre van a OpenAI)
- **Solución**: Complexity Router de Lemma para rutear queries simples a modelos baratos/rápidos

### 2. Costos Elevados de Tokens
- **Síntoma**: Factura OpenAI alta
- **Diagnóstico**:
  ```bash
  curl http://localhost:8004/api/v1/ai/evaluate
  # Response: { "total_tokens": 150000, "estimated_cost": 0.45, "avg_latency_ms": 1200 }
  ```
- **Causas probables**: 
  - RAG recuperando documentos muy grandes sin chunking adecuado
  - System prompt demasiado largo
  - Cache semántico de Lemma no configurado
- **Solución**: 
  - Activar squeeze_prompt de Lemma
  - Cache semántico (CARS de Lemma)
  - Chunking de documentos a 500 chars

### 3. Rate Limiting de APIs
- **Síntoma**: Errores 429 en logs de ai-agent-service
- **Diagnóstico**:
  ```bash
  docker-compose logs ai-agent-service | grep "429\|RateLimitError"
  ```
- **Causas probables**: 
  - Demasiadas queries concurrentes sin control
  - Límite de RPM (requests per minute) de OpenAI excedido
- **Solución**:
  - Implementar rate limiting en AI Agent Service (Redis-based)
  - Cola de requests con RabbitMQ
  - Lemma ya maneja rate limiting automáticamente

## Plan de Comunicación a Stakeholders

### 1. Alerta Inicial (primeros 5 min)
**A quien**: Líder técnico + PM
**Formato**: Canal de incidentes (Slack/Teams)
**Contenido**:
```
🚨 INCIDENTE REPORTADO
Severidad: Alta
Síntomas:
  - Usuarios no pueden guardar registros (500 en User Service)
  - Latencia alta en AI Agent (>30s)
  - Error rate: ~40% en últimas llamadas

Estado: Diagnosticando
Responsable: [Nombre]
```

### 2. Actualización de Diagnóstico (15 min)
**A quien**: Mismo canal + stakeholders afectados
**Contenido**:
```
🔍 DIAGNÓSTICO EN CURSO
Hallazgos iniciales:
  - PostgreSQL connection pool al 100% → sospecha de conexiones no liberadas
  - RabbitMQ queue "ai.events" con 5000+ mensajes sin procesar
  - OpenAI rate limit alcanzado (429 en últimos 10 min)

Acciones:
  1. Escalando pool de conexiones PG de 10 a 50
  2. Reiniciando consumer de Audit Service
  3. Activando rate limiting en AI Agent Service

ETA estimado: 30 min
```

### 3. Resolución
**A quien**: Todos los stakeholders
**Contenido**:
```
✅ INCIDENTE RESUELTO
Duración: 25 min
Causa raíz:
  1. Connection pool de PostgreSQL insuficiente (agotado por queries lentas de AI Agent)
  2. Efecto cascada: PG lento → Auth Service timeout → User Service falla → 500
  3. AI Agent sin rate limiting → OpenAI 429 → retries infinitos → empeora todo

Acciones correctivas:
  - Pool connections: 10 → 50 (configuración)
  - Rate limiting: 10 req/min por usuario en AI Agent
  - Circuit breaker: timeout de 5s en llamadas entre servicios
  - Monitoreo: alerta cuando pool >80%
  - Lemma: activar semantic cache para reducir llamadas a OpenAI
```

### Priorización de Acciones

```
1. ⚠️ Restaurar servicio (stop AI Agent temporalmente si es necesario)
2. 🔍 Diagnosticar causa raíz (logs, health checks, métricas)
3. 🛠️ Aplicar fix temporal (escalar pool, reiniciar consumer)
4. 📊 Monitorear estabilidad
5. 🔧 Aplicar fix permanente (configuración, code changes)
6. 📝 Post-mortem + acciones preventivas
```
