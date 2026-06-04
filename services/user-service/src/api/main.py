import asyncio
import json

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import Settings
from src.infrastructure.database import init_db, close_db
from src.infrastructure.message_queue import EventPublisher, EventConsumer
from src.api.routes.user_routes import router as user_router
from src.api.routes.role_routes import router as role_router

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app_settings = Settings()
app_event_publisher = EventPublisher(app_settings.rabbitmq_url)
app_event_consumer = None
_sync_user_use_case = None

app = FastAPI(
    title="User Service",
    description="User management microservice",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(role_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": app_settings.service_name}


async def handle_user_registered(routing_key: str, body: dict):
    from src.infrastructure.database import async_session_factory
    from src.infrastructure.database.repositories import SQLAlchemyUserRepository
    from src.application.use_cases.user_use_cases import SyncUserUseCase

    async with async_session_factory() as session:
        repo = SQLAlchemyUserRepository(session)
        use_case = SyncUserUseCase(repo)
        await use_case.execute(
            user_id=body.get("user_id"),
            email=body.get("email", ""),
            username=body.get("username", ""),
        )


@app.on_event("startup")
async def startup():
    global app_event_publisher, app_event_consumer
    logger.info("starting_user_service")
    await init_db(app_settings)
    await app_event_publisher.connect()
    app_event_consumer = EventConsumer(app_settings.rabbitmq_url, handle_user_registered)
    asyncio.create_task(app_event_consumer.start())
    logger.info("user_service_started")


@app.on_event("shutdown")
async def shutdown():
    global app_event_consumer
    logger.info("shutting_down_user_service")
    await close_db()
    await app_event_publisher.close()
    if app_event_consumer:
        await app_event_consumer.close()
    logger.info("user_service_shutdown")
