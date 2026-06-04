import json
from typing import Callable, Awaitable

import structlog
from aio_pika import connect_robust, IncomingMessage, ExchangeType

logger = structlog.get_logger(__name__)


class RabbitMQConsumer:
    def __init__(self, amqp_url: str = "amqp://guest:guest@rabbitmq:5672/"):
        self._amqp_url = amqp_url
        self._connection = None
        self._channel = None
        self._queue = None
        self._exchange = None
        self._consumer_tag = None

    async def connect(self) -> None:
        self._connection = await connect_robust(self._amqp_url)
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange("toka.events", ExchangeType.TOPIC, durable=True)
        self._queue = await self._channel.declare_queue("audit.all_events", durable=True)
        await self._queue.bind(self._exchange, routing_key="#")
        await logger.ainfo("rabbitmq_consumer_connected", queue="audit.all_events")

    async def disconnect(self) -> None:
        if self._consumer_tag and self._channel:
            await self._channel.cancel(self._consumer_tag)
        if self._connection:
            await self._connection.close()
            await logger.ainfo("rabbitmq_consumer_disconnected")

    async def start_consuming(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        if not self._channel:
            await self.connect()

        async def on_message(message: IncomingMessage) -> None:
            async with message.process():
                try:
                    payload = json.loads(message.body.decode())
                    await callback(payload)
                except Exception as e:
                    await logger.aerror("rabbitmq_consumer_error", error=str(e))

        self._consumer_tag = await self._queue.consume(on_message)
        await logger.ainfo("rabbitmq_consumer_started")
