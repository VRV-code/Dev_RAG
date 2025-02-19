from api.app.config import config, EMBEDDING_MODEL

def get_size_for_embedding(embedding_model: str):
    if embedding_model == EMBEDDING_MODEL.EMBASS:
        return 1024
    elif embedding_model == EMBEDDING_MODEL.MINILM:
        return 384
    elif embedding_model == EMBEDDING_MODEL.BAAI:
        return 1024
    elif embedding_model == EMBEDDING_MODEL.INFLOAT:
        return 1024
    elif embedding_model == EMBEDDING_MODEL.MXBAI:
        return 512
    else:
        return 768
