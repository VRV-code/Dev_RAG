import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import UniqueConstraint
import sqlalchemy.dialects.postgresql as pg
from sqlmodel import Column, Field, Relationship, SQLModel


# class User(SQLModel, table=True):
#     __tablename__ = "users"

#     uid: uuid.UUID = Field(sa_column=Column(pg.UUID, nullable=False, primary_key=True, default=uuid.uuid4))
#     username: str
#     created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
#     updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))

#     files: List["FileRag"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})

#     def __repr__(self):
#         return f"<User {self.username}>"


class FileRag(SQLModel, table=True):
    __tablename__ = "files"
    __table_args__ = {
        'extend_existing': True,
    }

    uid: uuid.UUID = Field(sa_column=Column(pg.UUID, nullable=False, primary_key=True, default=uuid.uuid4))
    filename: str = Field(sa_column=Column(pg.TEXT, unique=True))
    # user_uid: Optional[uuid.UUID] = Field(default=None, foreign_key="users.uid")
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))

    # user: Optional[User] = Relationship(back_populates="files")
    # __table_args__ = (UniqueConstraint("filename", "user_uid", name="unique_filename_user"),)

    def __repr__(self):
        return f"<FileRag {self.filename}>"


class ChatLog(SQLModel, table=True):
    __tablename__ = "chat_logs"
    __table_args__ = {
        "extend_existing": True,
    }

    id: int = Field(default=None, primary_key=True)
    question: str = Field(sa_column=Column(pg.TEXT, unique=False))
    response: str = Field(sa_column=Column(pg.TEXT, unique=False))
    timestamp: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))

    def __repr__(self):
        return f"<FileRag {self.filename}>"
