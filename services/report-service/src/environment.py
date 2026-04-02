from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Configurações de conexão com o banco de dados PostgreSQL."""

    host: str = Field(default="localhost", validation_alias="DATABASE_HOST")
    port: int = Field(default=5432, validation_alias="DATABASE_PORT")
    user: str = Field(default="report_user", validation_alias="DATABASE_USER")
    password: str = Field(default="report_pass", validation_alias="DATABASE_PASSWORD")
    name: str = Field(default="report_db", validation_alias="DATABASE_NAME")

    @property
    def async_url(self) -> str:
        """Retorna a URL de conexão async para o PostgreSQL."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RabbitMQSettings(BaseSettings):
    """Configurações de conexão com o RabbitMQ."""

    host: str = Field(default="localhost", validation_alias="RABBITMQ_HOST")
    port: int = Field(default=5672, validation_alias="RABBITMQ_PORT")
    user: str = Field(default="guest", validation_alias="RABBITMQ_USER")
    password: str = Field(default="guest", validation_alias="RABBITMQ_PASSWORD")
    exchange_name: str = Field(default="analise.events", validation_alias="RABBITMQ_EXCHANGE_NAME")
    queue_name: str = Field(default="report-service.reports", validation_alias="RABBITMQ_QUEUE_NAME")

    @property
    def url(self) -> str:
        """Retorna a URL de conexão AMQP para o RabbitMQ."""
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/"


class AppSettings(BaseSettings):
    """Configurações gerais da aplicação."""

    service_name: str = Field(default="report-service", validation_alias="SERVICE_NAME")
    debug: bool = Field(default=False, validation_alias="DEBUG")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")


class Settings(BaseSettings):
    """Configuração principal que agrupa todas as sub-configurações."""

    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    rabbitmq: RabbitMQSettings = Field(default_factory=RabbitMQSettings)


def get_settings() -> Settings:
    """Factory para obter as configurações da aplicação."""
    return Settings()
