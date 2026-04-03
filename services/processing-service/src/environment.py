from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Configurações de conexão com o banco de dados PostgreSQL."""

    host: str = Field(default="localhost", validation_alias="DATABASE_HOST")
    port: int = Field(default=5432, validation_alias="DATABASE_PORT")
    user: str = Field(default="processing_user", validation_alias="DATABASE_USER")
    password: str = Field(default="processing_pass", validation_alias="DATABASE_PASSWORD")
    name: str = Field(default="processing_db", validation_alias="DATABASE_NAME")

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
    queue_name: str = Field(default="processing-service.pipeline", validation_alias="RABBITMQ_QUEUE_NAME")

    @property
    def url(self) -> str:
        """Retorna a URL de conexão AMQP para o RabbitMQ."""
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/"


class S3Settings(BaseSettings):
    """Configurações de conexão com o S3/LocalStack."""

    endpoint_url: str = Field(default="http://localhost:4566", validation_alias="S3_ENDPOINT_URL")
    access_key_id: str = Field(default="test", validation_alias="AWS_ACCESS_KEY_ID")
    secret_access_key: str = Field(default="test", validation_alias="AWS_SECRET_ACCESS_KEY")
    bucket_name: str = Field(default="archlens-diagramas", validation_alias="S3_BUCKET_NAME")
    region_name: str = Field(default="us-east-1", validation_alias="AWS_REGION")


class LLMSettings(BaseSettings):
    """Configurações para o LLM via LiteLLM Proxy."""

    base_url: str = Field(default="http://localhost:4000", validation_alias="LLM_BASE_URL")
    api_key: str = Field(default="sk-litellm", validation_alias="LLM_API_KEY")
    model_name: str = Field(default="archlens-vision", validation_alias="LLM_MODEL_NAME")
    temperature: float = Field(default=0.1, validation_alias="LLM_TEMPERATURE")
    max_tokens: int = Field(default=4096, validation_alias="LLM_MAX_TOKENS")


class AppSettings(BaseSettings):
    """Configurações gerais da aplicação."""

    service_name: str = Field(default="processing-service", validation_alias="SERVICE_NAME")
    debug: bool = Field(default=False, validation_alias="DEBUG")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")


class Settings(BaseSettings):
    """Configuração principal que agrupa todas as sub-configurações."""

    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    rabbitmq: RabbitMQSettings = Field(default_factory=RabbitMQSettings)
    s3: S3Settings = Field(default_factory=S3Settings)
    llm: LLMSettings = Field(default_factory=LLMSettings)


def get_settings() -> Settings:
    """Factory para obter as configurações da aplicação."""
    return Settings()
