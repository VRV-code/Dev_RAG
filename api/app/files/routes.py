from typing import Annotated, List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession
from api.app import logger

# from .schemas import FileRagCreateModel
from api.app.vector_db.schemas import FileForChunkModel
from api.app.vector_db.service import ChunkService, VectorDatabaseService
from api.app.db.main import get_session
from api.app.db.models import FileRag
from api.app.db.models import LLMRagRag
from .service import FileService

file_router = APIRouter()

file_service = FileService()
chunk_service = ChunkService()
vectordb_service = VectorDatabaseService()

@file_router.post(
    "/create_file",
    status_code=status.HTTP_201_CREATED,
    response_model=LLMRag,
)
@file_router.post(
    "/create_file",
    status_code=status.HTTP_201_CREATED,
    response_model=FileRag,
)
async def create_rag_data_from_file(
    file_data: UploadFile,
    postgredb_session: AsyncSession = Depends(get_session),
):
    try:

        # Log du fichier reçu
        logger.info(f"Nom du fichier : {file_data.filename}")
        print(f"Taille : {file_data.size} bytes")

        # Création du fichier
        new_file = await file_service.create_file(
            file_data=file_data, session=postgredb_session
        )

        # Log après la création du fichier
        logger.info(f"Fichier créé avec l'UID : {new_file.uid}")

        # Traitement des chunks
        new_file_for_chunk = FileForChunkModel(
            str_file_content=file_service.parsed_file,
            dict_file_metadata={"filename": new_file.uid},
        )

        # chunk_service.create_chunks(file_for_chunk_data=new_file_for_chunk)
        chunk_service.create_chunks_from_text(file_for_chunk_data=new_file_for_chunk)
        vectordb_service.create_vectors(chunks=chunk_service.chunks)

        # Log succès
        logger.info("Chunks et vecteurs créés avec succès")

        return new_file
    except Exception as e:
        print(f"Erreur rencontrée : {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@file_router.get("/files/")
async def get_files(
    session: AsyncSession = Depends(get_session),
):
    # Class à retourner
    return await file_service.get_all_files(session=session)


@file_router.get("/files/{file_id}")
async def get_file_by_id(
    file_id: str,
    session: AsyncSession = Depends(get_session),
):
    # Class à retourner
    return await file_service.get_file(file_uid=file_id, session=session)


@file_router.delete("/delete_file", status_code=status.HTTP_201_CREATED)
async def delete_file(file_id: str, session: AsyncSession = Depends(get_session)):

    vectordb_service.delete_vectors(key="metadata.filename", value=file_id)
    await file_service.delete_file(file_uid=file_id, session=session)

    return f"The file {file_id} is removed"


@file_router.delete("/delete_files", status_code=status.HTTP_201_CREATED)
async def delete_files(
    file_ids: List[str], session: AsyncSession = Depends(get_session)
):

    for file_id in file_ids:
        vectordb_service.delete_vectors(key="metadata.filename", value=file_id)
        await file_service.delete_file(file_uid=file_id, session=session)

    return "All files are deleted"
