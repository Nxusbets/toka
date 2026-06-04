import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import Settings
from src.infrastructure.database import init_db, close_db
from src.infrastructure.cache import init_redis, close_redis
from src.infrastructure.message_queue import EventPublisher
from src.api.routes.auth_routes import router as auth_router

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

app = FastAPI(
    title="Auth Service",
    description="Authentication and authorization microservice",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": app_settings.service_name}


@app.on_event("startup")
async def startup():
    global app_event_publisher
    logger.info("starting_auth_service")
    await init_db(app_settings)
    await init_redis(app_settings)
    await app_event_publisher.connect()
    logger.info("auth_service_started")


@app.on_event("shutdown")
async def shutdown():
    logger.info("shutting_down_auth_service")
    await close_db()
    await close_redis()
    await app_event_publisher.close()
    logger.info("auth_service_shutdown")
