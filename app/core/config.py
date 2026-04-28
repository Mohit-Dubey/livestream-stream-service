from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "stream-service"
    DEBUG: bool = False

    # MongoDB
    MONGO_URL: str = "mongodb://localhost:27017"
    MONGO_DB: str = "streamdb"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    STREAM_EVENTS_EXCHANGE: str = "stream_events"
    USER_EVENTS_QUEUE: str = "stream-service.user-events"

    # Ant Media Server Enterprise
    ANT_MEDIA_URL: str = "http://your-ec2-ip:5080"
    ANT_MEDIA_APP: str = "LiveApp"
    ANT_MEDIA_USER: str = "admin"
    ANT_MEDIA_PASSWORD: str = "change-me"

    # User Service (internal)
    USER_SERVICE_URL: str = "http://user-service:8000"

    class Config:
        env_file = ".env"


settings = Settings()
