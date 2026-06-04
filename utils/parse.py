import os
import tempfile

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from database.db_manager import get_vector_store


def _load_pages_from_bytes(file_name, file_bytes):
    suffix = os.path.splitext(file_name)[1] or ".pdf"
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        loader = PyPDFLoader(temp_path)
        return loader.load()
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def index_pdf(file_name, file_bytes, document_id):
    pages = _load_pages_from_bytes(file_name, file_bytes)
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    chunks = splitter.split_documents(pages)

    for i, chunk in enumerate(chunks):
        chunk.metadata["document_id"] = str(document_id)
        chunk.metadata["filename"] = os.path.basename(file_name)
        chunk.metadata["chunk_index"] = i

    vector_store = get_vector_store()
    vector_store.add_documents(chunks)
    return len(chunks)


def delete_pdf(document_id):
    vector_store = get_vector_store()
    vector_store.delete(where={"document_id": str(document_id)})

MIN_TOP_K = 4
MAX_TOP_K = 6

def get_dynamic_top_k(question: str) -> int:
    """
    Decide how many chunks to retrieve based on the question.
    Always capped at MAX_TOP_K.
    """

    question_lower = question.lower()
    word_count = len(question.split())

    broad_keywords = [
        "summarize",
        "summary",
        "overview",
        "explain",
        "compare",
        "difference",
        "list",
        "main points",
        "key points",
        "what are",
        "describe",
    ]

    specific_keywords = [
        "when",
        "where",
        "who",
        "how much",
        "what is the date",
        "page",
    ]

    # Broad questions usually need more context
    if any(keyword in question_lower for keyword in broad_keywords):
        return MAX_TOP_K

    # Very short factual questions usually need fewer chunks
    if any(keyword in question_lower for keyword in specific_keywords):
        return MIN_TOP_K

    # Longer questions usually need slightly more context
    if word_count > 12:
        return MAX_TOP_K

    return MIN_TOP_K
