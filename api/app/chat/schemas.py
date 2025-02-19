from pydantic import BaseModel


class Response(BaseModel):
    content: str
    response_time: str
    documents: list


class Question(BaseModel):
    content: str
