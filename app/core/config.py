from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    temp_folder: str = "uploads"
    max_image_size_mb: int = 10
    log_level: str = "INFO"


settings = Settings()
