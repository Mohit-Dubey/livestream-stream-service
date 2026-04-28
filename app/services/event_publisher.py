import json
import logging
import aio_pika
from app.core.config import settings

logger = logging.getLogger(__name__)


async def publish_stream_event(event_type: str, payload: dict) -> None:
    """Publish a stream domain event to RabbitMQ (fire-and-forget)."""
    try:
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                settings.STREAM_EVENTS_EXCHANGE,
                aio_pika.ExchangeType.FANOUT,
                durable=True,
            )
            body = json.dumps({"event": event_type, "data": payload}).encode()
            await exchange.publish(
                aio_pika.Message(
                    body=body,
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key="",
            )
            logger.info(f"Published stream event: {event_type}")
    except Exception as exc:
        logger.warning(f"Failed to publish stream event {event_type}: {exc}")
