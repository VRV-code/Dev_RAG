from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
import base64
import io
from api.app.db.main import get_session
from .service import LLMService
from api.app.vector_db.service import VectorDatabaseService
from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import Question, Response
from time import time
from api.app.db.models import ChatLog
from api.app.config import config, Path


llm_router = APIRouter()


class ModelNotFoundError(Exception):
    def __init__(self, model_path: Path = config.MODEL_PATH):
        self.model_path = model_path

    def __str__(self):
        return f"Le fichier spécifié pour le modèle est introuvable : {self.model_path}"


@llm_router.post("/chat/", response_model=Response)
async def ask_question(
    question: Question,
    placeholder=None,
    llm: LLMService = Depends(LLMService),
    dbclient: VectorDatabaseService = Depends(VectorDatabaseService),
    session: AsyncSession = Depends(get_session),
):

    try:
        documents = dbclient.search_best_chunks(question.content)
        start_time = time()

        model_path = config.MODEL_PATH
        # print("CHEMIN", model_path.resolve())
        if not model_path.exists():
            raise ModelNotFoundError()

        response_content = llm.generate_response(
            question.content, documents, placeholder
        )
        end_time = time()

        duration = str(end_time - start_time)

        new_chat_log = ChatLog(question=question.content, response=response_content)
        session.add(new_chat_log)
        await session.commit()  # <---- a revoir
        # await session.refresh(new_chat_log)

    except ModelNotFoundError as e:
        await session.rollback()
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération de réponse : {str(e)}",
        )

    else:

        return Response(
            content=new_chat_log.response, response_time=duration, documents=documents
        )


@llm_router.get("/telecharger/{filename}")
async def download_file(filename: str):
    chemin_pdf = config.PDF_FOLDER / f"{filename}"
    if chemin_pdf.exists():
        return FileResponse(
            chemin_pdf,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={chemin_pdf.name}"},
        )
    else:
        return {"message": "Fichier non trouvé"}, 404


@llm_router.get("/afficher/{filename}")
async def display_file(filename: str):
    # Vérifiez si le fichier existe avant de le servir
    chemin_pdf = config.PDF_FOLDER / f"{filename}"
    if chemin_pdf.exists():
        # Utilisez le type MIME approprié pour le PDF
        return FileResponse(chemin_pdf, media_type="application/pdf")
    else:
        return {"message": "Fichier non trouvé"}, 404
