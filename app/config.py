from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    max_upload_size_mb: int = 50
    upload_dir: str = "uploads"
    database_url: str = "sqlite:///./documents.db"

    model_config = {"env_file": ".env"}


settings = Settings()
