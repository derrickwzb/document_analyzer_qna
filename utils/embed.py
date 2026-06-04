from langchain_huggingface import HuggingFaceEmbeddings

def get_embedding_model():
    # Create the embedding model used for document chunk vectors.
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
