from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    temp_folder: str = "uploads"
    max_image_size_mb: int = 10
    log_level: str = "INFO"

    # API Security
    api_token: str = "dev_token_123"
    docs_username: str = "admin"
    docs_password: str = "admin"


settings = Settings()
