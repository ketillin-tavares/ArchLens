from src.infrastructure.messaging.publisher import RabbitMQPublisher

rabbitmq_publisher = RabbitMQPublisher()
"""Instância global singleton do publisher RabbitMQ, usada pelo controller e main."""
