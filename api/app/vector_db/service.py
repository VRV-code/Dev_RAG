import re
from typing import Dict, List, Optional
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import torch
from api.app.config import config
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter

from uuid import uuid4
import logging

from api.app.vector_db.schemas import ChunkCreateModel, FileForChunkModel
from . import get_size_for_embedding

logging.basicConfig(level=logging.INFO)

print("Initialisation du modèle d'embedding...", config.EMBEDDING_MODEL)
with torch.cuda.device(1):
    EmbeddingForChunks = SentenceTransformer(
        model_name_or_path=config.EMBEDDING_MODEL, device="cuda:1" if torch.cuda.is_available() else "cpu"
    )


class ChunkService:
    def __init__(self):
        self.chunks = None

    def create_chunks(
        self,
        file_for_chunk_data: FileForChunkModel,
        max_chunk_size: int = config.CHUNKS.SIZE,
        chunk_overlap: int = config.CHUNKS.OVERLAP,
    ):
        """
        Découpe une liste de Documents en chunks plus petits tout en conservant les métadonnées.

        Args:
            documents (List[Document]):
                Liste d'objets `Document` contenant le contenu (`content`) et les métadonnées (`metadata`).
            max_chunk_size (int):
                Taille maximale d'un chunk en caractères.
            chunk_overlap (int):
                Nombre de caractères à chevaucher entre deux chunks adjacents.

        Returns:
            List[Document]:
                Une liste de nouveaux objets `Document` représentant les chunks découpés. Chaque chunk conserve
                les métadonnées du document original et inclut des informations supplémentaires, comme
                l'index du chunk et l'index du document d'origine.
        """
        self.chunks = []  # Liste qui va contenir les chunks créés

        sections = re.split(
            r"\n##\s*", file_for_chunk_data.str_file_content
        )  # Découpe le texte en sections à chaque titre Markdown "##"
        buffer = sections[0]  # Le premier chunk contient la première section

        # Si le document n'a qu'une seule section, ajoute cette section comme un chunk unique
        if len(sections) == 1:
            self.chunks.append(
                ChunkCreateModel(
                    content=buffer,
                    metadata={
                        **file_for_chunk_data.dict_file_metadata,
                        "chunk_index": 0,
                    },
                )
            )
            return None

        # Si le document contient plusieurs sections, on procède au découpage
        for i in range(1, len(sections)):
            next_section = sections[i]  # La section suivante à ajouter au buffer

            # Si la taille du buffer dépasse la taille maximale d'un chunk, on ajoute un chevauchement du chunk suivant
            if len(buffer) >= max_chunk_size:
                buffer += next_section[
                    :chunk_overlap
                ]  # Ajoute une partie de la section suivante avec overlap
                self.chunks.append(
                    ChunkCreateModel(
                        content=buffer,
                        metadata={
                            **file_for_chunk_data.dict_file_metadata,  # Conserve les métadonnées originales
                            "chunk_index": len(
                                self.chunks
                            ),  # Index du chunk dans la liste
                        },
                    )
                )

                # Le buffer devient la section suivante après l'overlap
                buffer = (
                    next_section[chunk_overlap:]
                    if i == len(sections) - 1  # Si c'est la dernière section
                    else next_section  # Sinon, on garde la section suivante
                )
            # Si l'ajout de la section suivante dépasse la tolérance de taille, on ajoute un chunk
            elif (
                len(buffer) + len(next_section) + chunk_overlap
                >= config.CHUNK_TOLERANCE_FACTOR * max_chunk_size
            ):
                buffer += next_section[
                    :chunk_overlap
                ]  # Ajoute une partie de la section suivante avec overlap
                self.chunks.append(
                    ChunkCreateModel(
                        content=buffer,
                        metadata={
                            **file_for_chunk_data.dict_file_metadata,
                            "chunk_index": len(self.chunks),
                        },
                    )
                )
                # Le buffer devient la section suivante après l'overlap
                buffer = (
                    next_section[chunk_overlap:]
                    if i == len(sections) - 1
                    else next_section
                )
            else:
                # Sinon, on continue d'ajouter la section au buffer si la taille est dans les limites
                buffer += next_section

            # Si c'est la dernière section et que le buffer contient encore du texte, ajoute-le comme un chunk
            if i == len(sections) - 1 and buffer:
                self.chunks.append(
                    ChunkCreateModel(
                        content=buffer,
                        metadata={
                            **file_for_chunk_data.dict_file_metadata,
                            "chunk_index": len(self.chunks),
                        },
                    )
                )

        return None

    # def create_chunks_from_text(
    #     self,
    #     file_for_chunk_data: FileForChunkModel,
    #     chunk_size: int = config.CHUNKS.SIZE,
    #     chunk_overlap: int = config.CHUNKS.OVERLAP,):
    #     """
    #     Découpe une liste de Documents en chunks plus petits tout en conservant les métadonnées.
    #     """
    #     from langchain.text_splitter import RecursiveCharacterTextSplitter

    #     text_splitter = RecursiveCharacterTextSplitter(
    #         chunk_size=chunk_size,
    #         chunk_overlap=chunk_overlap,
    #     )

    #     chunks = text_splitter.create_documents([file_for_chunk_data.str_file_content])
    #     self.chunks = list()

    #     for i, chunk in enumerate(chunks):
    #         self.chunks.append(
    #             ChunkCreateModel(
    #                 content=chunk.page_content,
    #                 metadata={
    #                     **file_for_chunk_data.dict_file_metadata,
    #                     "chunk_index": i,
    #                 },
    #             )
    #         )
    #     return

    # def create_chunks_from_text(
    #     self,
    #     file_for_chunk_data: FileForChunkModel,
    #     chunk_size: int = config.CHUNKS.SIZE,
    #     chunk_overlap: int = config.CHUNKS.OVERLAP,
    # ) -> None:
    #     """Divise un fichier Markdown en chunks tout en respectant les sections et la taille définie."""

    #     sections = re.split(r"(?=^## )", file_for_chunk_data.str_file_content, flags=re.MULTILINE)
    #     sections = [s.strip() for s in sections if s.strip()]
    #     self.chunks = []

    #     from langchain.text_splitter import RecursiveCharacterTextSplitter

    #     text_splitter = RecursiveCharacterTextSplitter(
    #         chunk_size=chunk_size,
    #         chunk_overlap=chunk_overlap,
    #     )

    #     for i, section in enumerate(sections):
    #         section_chunks = text_splitter.create_documents([section])
    #         self.chunks.extend(
    #             ChunkCreateModel(
    #                 content=chunk.page_content,
    #                 metadata={
    #                     **file_for_chunk_data.dict_file_metadata,
    #                     "chunk_index": f"{i}-{j}",
    #                 },
    #             )
    #             for j, chunk in enumerate(section_chunks)
    #         )

    #     return


    def create_chunks_from_text(
        self,
        file_for_chunk_data: FileForChunkModel,
        chunk_size: int = config.CHUNKS.SIZE,
        chunk_overlap: int = config.CHUNKS.OVERLAP,
    ) -> None:
        """Divise un fichier Markdown en chunks avec gestion des titres et sous-titres."""

        content = file_for_chunk_data.str_file_content.strip()
        self.chunks = []

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        # Vérifier d'abord si le texte contient des titres principaux `# `
        if "#" in content:
            main_sections = re.split(r"(?=^# )", content, flags=re.MULTILINE)
        else:
            main_sections = [
                content
            ]  # Aucun titre principal, traiter comme une seule section

        for main_section in main_sections:
            main_lines = main_section.strip().split("\n")
            main_title = (
                main_lines[0] if main_lines and main_lines[0].startswith("# ") else ""
            )
            main_body = "\n".join(main_lines[1:]) if main_title else main_section

            if "##" in main_body:
                sub_sections = re.split(r"(?=^## )", main_body, flags=re.MULTILINE)
            else:
                sub_sections = [
                    main_body
                ]  # Pas de sous-titres, traiter comme une seule sous-section

            for sub_section in sub_sections:
                sub_lines = sub_section.strip().split("\n")
                sub_title = (
                    sub_lines[0] if sub_lines and sub_lines[0].startswith("## ") else ""
                )
                sub_body = "\n".join(sub_lines[1:]) if sub_title else sub_section

                if sub_body.strip():  # Ignorer les sections vides
                    section_chunks = text_splitter.create_documents([sub_body])

                    for j, chunk in enumerate(section_chunks):
                        chunk_content = chunk.page_content
                        if j == 0:  # Ajouter les titres au premier chunk de la section
                            chunk_content = (
                                f"{main_title}\n{sub_title}\n\n{chunk_content}".strip()
                            )

                        self.chunks.append(
                            ChunkCreateModel(
                                content=chunk_content,
                                metadata={
                                    **file_for_chunk_data.dict_file_metadata,
                                    "chunk_index": f"{len(self.chunks)}",
                                },
                            )
                        )


class VectorDatabaseService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.initialized = True
            # self.client = QdrantClient(host=QDRANT.HOST, port=QDRANT.PORT)
            self.client = QdrantClient(url=config.QDRANT_URL)

            if not self.client.collection_exists(
                collection_name=config.COLLECTION_NAME
            ):
                self.client.create_collection(
                    collection_name=config.COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=get_size_for_embedding(config.EMBEDDING_MODEL),
                        distance=Distance.COSINE,
                    ),
                )

            print("Modèle initialisé avec succès. -> (vectordb)")

    def __repr__(self):
        # Formater chaque ligne pour qu'elle soit bien alignée
        collection_name_line = f"COLLECTION_NAME = {config.COLLECTION_NAME}"
        host_line = f"CONNECTED TO QDRANT AT {config.QDRANT_URL}"
        return f"""\n{collection_name_line}\n{host_line}\n"""

    def search_best_chunks(self, query: str, k=config.NUMBER_BEST_CHUNKS):
        # Convert text query into vector
        vector = EmbeddingForChunks.encode(query).tolist()

        # Use `vector` for search for closest vectors in the collection
        search_result = self.client.query_points(
            collection_name=config.COLLECTION_NAME,
            query=vector,
            query_filter=None,
            limit=k,
        ).points

        payloads = [hit.payload for hit in search_result]
        return payloads

    def _create_vector(self, chunk: ChunkCreateModel):
        """Charge et ajoute des fichiers au magasin de vecteurs"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        uuid = str(uuid4())

        vector = EmbeddingForChunks.encode(chunk.content)

        self.client.upsert(
            collection_name=config.COLLECTION_NAME,
            points=[
                PointStruct(
                    id=uuid,
                    payload={
                        "content": chunk.content,
                        "metadata": chunk.metadata,
                    },
                    vector=vector,
                ),
            ],
        )

        return None

    def create_vectors(self, chunks: List[ChunkCreateModel]):
        for chunk in chunks:
            self._create_vector(chunk=chunk)

            logging.info(f"{len(chunks)} chunks ajoutés au magasin de vecteurs.")
            print(f"{len(chunks)} chunks ajoutés au magasin de vecteurs.")

    def delete_vectors(self, key, value):

        self.client.delete(
            collection_name=config.COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.filename",
                            match=models.MatchValue(value=value),
                        ),
                    ],
                )
            ),
        )
        pass

    def _rollback(self, operation: str):
        if operation == "post":
            self._delete_vectors()

            return

        elif operation == "delete":
            if self.backup_chunk_data is not None and len(self.backup_chunk_data) > 0:
                self.client.upsert(
                    collection_name=config.COLLECTION_NAME,
                    points=self.backup_chunk_data,
                )

            return

    def commit(self, operation: str):
        if operation == "post":
            try:
                self.client.upsert(
                    collection_name=config.COLLECTION_NAME,
                    points=self.vectors,
                )

                logging.info(
                    f"{len(self.vectors)} chunks ajoutés au magasin de vecteurs."
                )
                print(f"{len(self.vectors)} chunks ajoutés au magasin de vecteurs.")

            except Exception as e:
                print(f"Erreur : {e}")
                self._rollback(operation="post")

                raise

        elif operation == "delete":
            try:
                self._get_vectors()
                self._delete_vectors()

            except Exception as e:
                print(f"Erreur : {e}")
                self._rollback(operation="delete")

                raise
