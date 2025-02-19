from fastapi import FastAPI
from api.app.files.routes import file_router
# from .db.routes import postgresdb_router
from api.app.chat.routes import llm_router
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from api.app.db.main import init_db, close_db
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()  # Appelé au démarrage
    try:
        yield
    finally:
        await close_db()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # Permet toutes les origines (vous pouvez restreindre à certaines origines si nécessaire)
    allow_credentials=True,
    allow_methods=["*"],  # Permet toutes les méthodes HTTP
    allow_headers=["*"],  # Permet tous les en-têtes
)

# app.include_router(postgresdb_router)
app.include_router(file_router)
app.include_router(llm_router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}


if __name__ == "__main__":
    uvicorn.run("testapp:app", host="127.0.0.1", port=8000, log_level="info", workers=1, reload=True)
