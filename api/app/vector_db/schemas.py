from typing import Dict
from pydantic import BaseModel


class FileForChunkModel(BaseModel):
    str_file_content: str
    dict_file_metadata: Dict

class ChunkCreateModel(BaseModel):
    content: str
    metadata: Dict

