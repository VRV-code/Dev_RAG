import io
import os
import mimetypes

from docling_core.types.doc import ImageRefMode, PictureItem, TableItem
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    AcceleratorOptions,
    AcceleratorDevice,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.models.tesseract_ocr_model import TesseractOcrOptions
from docling.document_converter import DocumentStream
from fastapi import UploadFile, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import desc, select

from docling.datamodel.base_models import InputFormat

from api.app.db.models import FileRag
from api.app.db.models import LLMRag

from api.app import logger


class LocalFileService:
    def create_local_file(self, filename: str, file_bytes_stream: bytes):
        user_folder_path = "dossier"

        if not os.path.isdir(user_folder_path):
            os.mkdir(user_folder_path)

        # Enregistrer le fichier localement
        user_file_path = f"{user_folder_path}/{filename}"
        with open(user_file_path, "wb") as text_wrapper:
            text_wrapper.write(file_bytes_stream)

        print(f"Le fichier {filename} a été sauvegardé avec succès.")
        return

    # def update_local_file(self, filename: str, file_bytes_stream: bytes):
    #     with open(filename, 'wb') as text_wrapper:
    #         text_wrapper.write(file_bytes_stream)
    #     return None

    def delete_local_file(self, filename: str):
        user_folder_path = f"dossier"
        user_file_path = f"{user_folder_path}/{filename}"

        os.remove(path=user_file_path)
        return None


local_file = LocalFileService()


class FileService:
    """
    Classe générique pour l'extraction des informations des documents
    Elle prends en charge : pdf, pdf scanné, docx, xlsx, markdown, png, jpg (png et jpg de qualité moindre)

    Attributs-donnée:
        - file (UploadFile): Le type de fichier obtenu quand on entre un document via FastAPI
        - converter (func): Fonction Docling pour transformer un document source en DoclingDocument

    Attributs-méthode:
        - content_from_file (async object method)

        - content_as_markdown_for_prompting (static method)
        - save_markdown_to_local_storage (static method)
        - read_markdown_from_local_storage (static method)
    """

    def __init__(self, converter=DocumentConverter):
        pipeline_options = PdfPipelineOptions()
        # pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.do_cell_matching = True
        # pipeline_options.ocr_options = TesseractOcrOptions()
        pipeline_options.accelerator_options = AcceleratorOptions(
            num_threads=4, device=AcceleratorDevice.AUTO
        )
        self.converter = converter(
            allowed_formats=[
                InputFormat.DOCX,
                InputFormat.PPTX,
                InputFormat.HTML,
                InputFormat.IMAGE,
                InputFormat.PDF,
                InputFormat.ASCIIDOC,
                InputFormat.MD,
                InputFormat.XLSX,
            ],
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            },
        )
        self.parsed_file = None

    @staticmethod
    async def get_all_files(session: AsyncSession):
        statement = select(FileRag).order_by(desc(FileRag.created_at))

        result = await session.exec(statement)

        return result.all()

    async def get_file(self, file_uid: str, session: AsyncSession):
        statement = select(FileRag).where(FileRag.uid == file_uid)

        result = await session.exec(statement)

        file = result.first()

        return file if file is not None else None

    async def create_file(
        self, file_data: UploadFile, session: AsyncSession, export_to: str = "markdown"
    ) -> FileRag:
        # Extraire le contenu sous forme de bytes
        file_bytes_stream = file_data.file.read()
        # logger.info(f"FILES_BYTES: {file_bytes_stream} bytes")

        logger.info(
            f"Fichier {file_data.filename} détecté avec extension {file_data.filename.split('.')[-1]}"
        )

        # Enregistrement du fichier localement
        local_file.create_local_file(
            filename=file_data.filename, file_bytes_stream=file_bytes_stream
        )

        source = DocumentStream(
            name=file_data.filename, stream=io.BytesIO(file_bytes_stream)
        )
        logger.debug(f"Fichier {file_data.filename} prêt pour la conversion.")
        try:
            docling_document_from_file = self.converter.convert(source).document
        except Exception as e:
            logger.error(
                f"Erreur de conversion pour le fichier {file_data.filename}: {e}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Format de fichier non pris en charge: {file_data}",
            )

        # Enregistrement du fichier dans la base de données
        if export_to == "markdown":
            self.parsed_file = docling_document_from_file.export_to_markdown(
                image_mode=ImageRefMode.REFERENCED
            )
            converted_file_extension = "md"
        elif export_to == "html":
            self.parsed_file = docling_document_from_file.export_to_html()

        new_file = FileRag(filename=file_data.filename)
        session.add(new_file)
        await session.commit()

        return new_file

    async def delete_file(self, file_uid: str, session: AsyncSession):
        file_to_delete = await self.get_file(file_uid, session)

        # Delete en local
        local_file.delete_local_file(filename=file_to_delete.filename)

        # Delete de la db PostgreSQL
        if file_to_delete is not None:
            await session.delete(file_to_delete)

            await session.commit()


    async def create_llm(
        self, file_data: UploadFile, session: AsyncSession, export_to: str = "markdown"
    ) -> LLMRag:
        # Extraire le contenu sous forme de bytes
        file_bytes_stream = file_data.file.read()
        # logger.info(f"FILES_BYTES: {file_bytes_stream} bytes")

        logger.info(
            f"Fichier {file_data.filename} détecté avec extension {file_data.filename.split('.')[-1]}"
        )

        # Enregistrement du fichier localement
        local_file.create_local_llm(
            llmname=file_data.llmname, llm_bytes_stream=file_bytes_stream
        )

        source = DocumentStream(
            name=file_data.llmname, stream=io.BytesIO(file_bytes_stream)
        )
        logger.debug(f"Fichier {file_data.llmname} prêt pour la conversion.")
        try:
            docling_document_from_llm = self.converter.convert(source).document
        except Exception as e:
            logger.error(
                f"Erreur de conversion pour le fichier {file_data.llmname}: {e}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Format de fichier non pris en charge: {file_data}",
            )

        # Enregistrement du fichier dans la base de données
        if export_to == "markdown":
            self.parsed_llm = docling_document_from_llm.export_to_markdown(
                image_mode=ImageRefMode.REFERENCED
            )
            converted_lmm_extension = "md"
        elif export_to == "html":
            self.parsed_llm = docling_document_from_llm.export_to_html()

        new_llm = LLMRag(llmname=file_data.llmname)
        session.add(new_llm)
        await session.commit()

        return new_llm

    async def delete_llm(self, llm_uid: str, session: AsyncSession):
        llm_to_delete = await self.get_llm(llm_uid, session)

        # Delete en local
        local_file.delete_local_llm(lmm=llm_to_delete.llmname)

        # Delete de la db PostgreSQL
        if llm_to_delete is not None:
            await session.delete(llm_to_delete)

            await session.commit()