from typing import Type
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# importing necessary functions from dotenv library

from enum import Enum


class EMBEDDING_MODEL(Enum):
    EMBASS: str = "embaas/sentence-transformers-e5-large-v2"
    MINILM: str = "all-MiniLM-L6-v2"
    BAAI: str = "BAAI/bge-large-en-v1.5"
    INFLOAT: str = "intfloat/multilingual-e5-large"
    MXBAI: str = "mixedbread-ai/mxbai-embed-large-v1"

    def __str__(self):
        return self.value


class Chunks(BaseModel):
    SIZE: int = 1000
    OVERLAP: int = 500

    def __str__(self):
        return self.value


config_2dir = Path(__file__).parent.parent


# print(config_dir)
class Settings(BaseSettings):
    DATABASE_URL: str
    QDRANT_URL: str
    FASTAPI_URL: str
    COLLECTION_NAME: str
    EMBEDDING_MODEL: str = (
        EMBEDDING_MODEL.MXBAI
    )  # EMBEDDING_MODEL.MINILM, EMBEDDING_MODEL.BAAI, EMBEDDING_MODEL.INFLOAT, EMBEDDING_MODEL.MXBAI
    CHUNKS: Chunks = Chunks()
    NUMBER_BEST_CHUNKS: float = 3
    CHUNK_TOLERANCE_FACTOR: float = 1.5
    MODEL_PATH: Path = config_2dir / "app/chat/llm_models/qwen2-7b-instruct-q5_k_m.gguf"
    PDF_FOLDER: Path = config_2dir / "dossier/"
    MODEL_FOLDER: Path = config_2dir / "app/chat/llm_models/"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


config = Settings()
# print("Settings initialized -> config", Settings().model_dump())
