import logging
import os
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from infrastructure.database import MongoDatabase
from infrastructure.database.repositories import MongoAuditLogRepository
from infrastructure.message_queue import RabbitMQConsumer
from application.use_cases.audit_use_cases import LogEventUseCase

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

mongo = MongoDatabase()
mq_consumer = RabbitMQConsumer(amqp_url=os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongo.connect()
    audit_repo = MongoAuditLogRepository(mongo.db)
    log_event_use_case = LogEventUseCase(audit_repo)

    app.state.audit_repo = audit_repo
    app.state.log_event_use_case = log_event_use_case

    await mq_consumer.connect()

    async def handle_event(event_data: dict) -> None:
        if log_event_use_case:
            await log_event_use_case.execute(event_data)

    await mq_consumer.start_consuming(handle_event)

    await logger.ainfo("audit_service_started")
    yield

    await mq_consumer.disconnect()
    await mongo.disconnect()
    await logger.ainfo("audit_service_stopped")


app = FastAPI(title="Audit Service", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "audit-service"}


from api.routes.audit_routes import router as audit_router
app.include_router(audit_router, prefix="/api/v1/audit")
