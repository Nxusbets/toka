import json

import structlog
from aio_pika import connect_robust, ExchangeType, Message

logger = structlog.get_logger(__name__)


class RabbitMQPublisher:
    def __init__(self, amqp_url: str = "amqp://guest:guest@rabbitmq:5672/"):
        self._amqp_url = amqp_url
        self._connection = None
        self._channel = None
        self._exchange = None

    async def connect(self) -> None:
        self._connection = await connect_robust(self._amqp_url)
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange("toka.events", ExchangeType.TOPIC, durable=True)
        await logger.ainfo("rabbitmq_publisher_connected")

    async def disconnect(self) -> None:
        if self._connection:
            await self._connection.close()
            await logger.ainfo("rabbitmq_publisher_disconnected")

    async def publish(self, routing_key: str, payload: dict) -> None:
        if not self._exchange:
            await self.connect()
        message = Message(
            body=json.dumps(payload).encode(),
            content_type="application/json",
            delivery_mode=2,
        )
        await self._exchange.publish(message, routing_key=routing_key)
        await logger.ainfo("rabbitmq_message_published", routing_key=routing_key)
