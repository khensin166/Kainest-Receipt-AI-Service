from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    groq_api_key: str = ""
    # Daftar model yang dirotasi otomatis (fallback). Pisahkan dengan koma.
    # Prioritas: llama-3.1-70b-versatile → llama-3.1-8b-instant
    groq_models: str = "llama-3.1-70b-versatile,llama-3.1-8b-instant,mixtral-8x7b-32768"
    groq_base_url: str = ""  # Opsional: biarkan kosong untuk API asli Groq
    temp_folder: str = "uploads"
    max_image_size_mb: int = 10
    log_level: str = "INFO"

    # API Security
    api_token: str = "dev_token_123"
    docs_username: str = "admin"
    docs_password: str = "admin"


settings = Settings()
