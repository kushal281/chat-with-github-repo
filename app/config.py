from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_api_key: str = ""
    llm_model: str = ""
    chroma_dir: str = "./chroma_data"
    max_file_kb: int = 200
    max_files: int = 2000
    clone_timeout_s: int = 60


settings = Settings()