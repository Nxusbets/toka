import logging
import os
from contextlib import asynccontextmanager

import httpx
import structlog
from fastapi import FastAPI

from infrastructure.database import QdrantDatabase
from infrastructure.database.repositories import QdrantVectorRepository, QueryLogRepositoryImpl
from infrastructure.external import LLMSettings, create_llm_client, create_embed_client
from infrastructure.message_queue import RabbitMQPublisher
from application.use_cases.ai_use_cases import QueryUseCase, IngestDocumentUseCase, ReportUseCase, EvaluateUseCase

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

qdrant = QdrantDatabase()
mq_publisher = RabbitMQPublisher(amqp_url=os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/"))
llm_settings = LLMSettings()
llm_client = create_llm_client(llm_settings)
embed_client = create_embed_client(llm_settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await qdrant.connect()
    await mq_publisher.connect()

    vector_repo = QdrantVectorRepository(qdrant.client)
    query_log_repo = QueryLogRepositoryImpl()
    http_client = httpx.AsyncClient(timeout=30.0)

    app.state.vector_repo = vector_repo
    app.state.query_log_repo = query_log_repo
    app.state.mq_publisher = mq_publisher

    app.state.query_use_case = QueryUseCase(vector_repo, query_log_repo, llm_client, embed_client)
    app.state.ingest_use_case = IngestDocumentUseCase(vector_repo, embed_client)
    app.state.report_use_case = ReportUseCase(llm_client, http_client, "http://user-service:8000")
    app.state.evaluate_use_case = EvaluateUseCase(query_log_repo)

    await logger.ainfo("ai_agent_service_started")
    yield

    await http_client.aclose()
    await mq_publisher.disconnect()
    await qdrant.disconnect()
    await logger.ainfo("ai_agent_service_stopped")


app = FastAPI(title="AI Agent Service", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-agent-service"}


from api.routes.ai_routes import router as ai_router
app.include_router(ai_router, prefix="/api/v1/ai")
