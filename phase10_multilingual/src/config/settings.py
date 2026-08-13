from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    translation_provider: str = "mock"
    openai_api_key: str = ""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
