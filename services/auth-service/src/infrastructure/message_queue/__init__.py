import json
from dataclasses import asdict
from typing import Optional

import aio_pika
from structlog import get_logger

logger = get_logger(__name__)


class EventPublisher:
    def __init__(self, rabbitmq_url: str):
        self.url = rabbitmq_url
        self.connection: Optional[aio_pika.abc.AbstractRobustConnection] = None
        self.channel: Optional[aio_pika.abc.AbstractChannel] = None
        self.exchange: Optional[aio_pika.abc.AbstractExchange] = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.url)
        self.channel = await self.connection.channel()
        self.exchange = await self.channel.declare_exchange(
            "toka.events", aio_pika.ExchangeType.TOPIC, durable=True
        )
        logger.info("rabbitmq_connected", exchange="toka.events")

    async def publish(self, event):
        body = json.dumps(asdict(event), default=str).encode()
        message = aio_pika.Message(body=body, content_type="application/json", delivery_mode=aio_pika.DeliveryMode.PERSISTENT)
        await self.exchange.publish(message, routing_key=event.event_type)
        logger.info("event_published", event_type=event.event_type)

    async def close(self):
        if self.connection:
            await self.connection.close()
            logger.info("rabbitmq_disconnected")
