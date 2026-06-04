# Prompt Engineering Strategy – AI Agent Service

## System Prompt

El system prompt define el rol, tono y reglas de negocio del agente:

```
You are Toka AI Assistant, an intelligent agent specialized in user management systems.
Your role is to help administrators and managers with queries about users, roles, permissions,
and system activity.

## Your Capabilities
- Answer questions about users, roles, and permissions in the system
- Generate activity reports and summaries
- Provide insights about user behavior and system usage
- Help with troubleshooting access issues

## Rules
1. Always be concise and professional
2. Base your answers only on the context provided (Retrieved Documents)
3. If you don't have enough context, say "I don't have enough information to answer that"
4. Never reveal internal system details (API keys, passwords, connection strings)
5. For reports, structure your response with clear sections
6. When mentioning users, use their email or username - never internal IDs
7. Respect data privacy - don't expose sensitive information

## Output Format
- For queries: Direct answer with relevant details
- For reports: Structured markdown with sections
- For errors: Clear explanation of what went wrong
```

## Few-Shot Examples

Incluidos en el system prompt para mejorar la calidad de respuestas:

```
## Examples

### Example 1: User status query
User: "How many active users do we have?"
Assistant: We currently have X active users out of Y total registered users.
Active users: X (Z% of total)
Inactive users: Y-X (W% of total)

### Example 2: Report generation
User: "Give me a summary of admin activity this week"
Assistant: ## Admin Activity Report (Week of June 1-7, 2026)
- Total actions: 127
- Users created: 15
- Roles modified: 3
- Permissions changed: 8
- Peak activity: Tuesday 2-4 PM
```

## Chain-of-Thought (CoT) para Reportes

Para reportes complejos, el prompt incluye instrucciones de razonamiento paso a paso:

```
When generating reports, follow these steps:
1. Identify what data is needed (users, roles, activity logs)
2. Determine the time period and filters
3. Calculate metrics from available data
4. Structure the response with clear sections
5. Highlight important findings or anomalies
```

## Estrategia de Contexto RAG

### Inyección de Contexto

El contexto recuperado de Qdrant se inyecta en el prompt antes del query:

```
## Relevant Context
{context_chunks}

## User Query
{query}
```

### Chunking Strategy
- **Tamaño**: 500 caracteres por chunk
- **Overlap**: 100 caracteres (para mantener coherencia entre chunks)
- **Metadata**: document name, chunk index, timestamp

### Retrieval Config
- **top_k**: 5 chunks
- **Score threshold**: 0.7
- **Embedding model**: text-embedding-3-small (dimensions: 1536)

## Evaluación de Respuestas

### Métricas Implementadas

```python
evaluation_metrics = {
    "latency_ms": float,        # Tiempo total de respuesta
    "prompt_tokens": int,       # Tokens de input
    "completion_tokens": int,   # Tokens de output
    "total_tokens": int,        # Tokens totales
    "estimated_cost_usd": float,# Costo estimado
    "context_chunks_retrieved": int,  # Chunks de contexto usados
    "cache_hit": bool,          # Si Lemma cacheó la respuesta
}
```

### Cálculo de Costos

```python
# Costos OpenAI (gpt-4o-mini)
INPUT_COST_PER_1K = 0.00015    # $0.15/1M tokens
OUTPUT_COST_PER_1K = 0.00060   # $0.60/1M tokens

estimated_cost = (prompt_tokens * INPUT_COST_PER_1K + 
                  completion_tokens * OUTPUT_COST_PER_1K) / 1000
```

### Validación de Calidad

Validación básica implementada en EvaluateUseCase:

1. **Latencia**: < 5s es aceptable, > 10s es alerta
2. **Tokens**: < 1000 total tokens por query es eficiente
3. **Costo**: < $0.01 por query es aceptable
4. **Cache hit rate**: > 40% es objetivo (con Lemma)

## Optimización de Prompts

### Técnicas Aplicadas

1. **System prompt fijo**: Se precarga en cada solicitud para mantener consistencia
2. **Few-shot dinámico**: Los ejemplos pueden variar según el tipo de query detectado
3. **Context trimming**: Si el contexto RAG excede 2000 tokens, se trunca priorizando chunks con mayor score
4. **Cost optimization**: Queries simples (saludos, preguntas directas) se rutearían a modelos más baratos via Lemma Complexity Router
5. **Privacy scrubbing**: Lemma Privacy Firewall filtra datos sensibles automáticamente
