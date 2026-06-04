

import os
from dotenv import load_dotenv
from groq import Groq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from utils.prompts import RAG_QA_PROMPT as SYSTEM_PROMPT

load_dotenv()

CHROMA_DIR   = "./chroma_rag_demo"      # Same dir as practice_02
MIN_TOP_K = 4
MAX_TOP_K = 6

# ── SETUP ──────────────────────────────────────────────────────────────────────
print("🔧 Setting up embedding model and vector store...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Load the existing ChromaDB index (no re-embedding needed)
vector_store = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings,
    collection_name="document_chunks",
)

# retriever = vector_store.as_retriever(search_kwargs={"k": TOP_K})
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

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

def format_context(docs):
    """Turn retrieved Document objects into a readable context string."""
    parts = []
    for i, doc in enumerate(docs, 1):
        page = doc.metadata.get("page", "?")
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[Source {i} | {source} | page {page}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)

def ask(question: str):
    print(f"\n{'='*60}")
    print(f"❓ Question: {question}")

    topk = get_dynamic_top_k(question)

    # Step 5: Retrieve
    retriever = vector_store.as_retriever(
        search_kwargs={"k": topk}
    )
    docs = retriever.invoke(question)
    print(f"\n📋 Retrieved {len(docs)} chunks:")
    for doc in docs:
        print(f"   • page {doc.metadata.get('page','?')} — {doc.page_content[:80]}...")

    # Step 6: Generate
    context = format_context(docs)
    prompt = f"""Question: {question}

                Retrieved context:
                {context}

                Answer using ONLY the context above. Include page references."""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.5,
        stream = True,
    )

    answer = response.choices[0].message.content
    print(f"top-k = {topk}")
    print(f"\n🤖 Answer:\n{answer}")
    return answer

# # ── INTERACTIVE LOOP ───────────────────────────────────────────────────────────
# print("\n✅ RAG pipeline ready. Type your questions (or 'quit' to exit).\n")
# while True:
#     question = input("Your question: ").strip()
#     if question.lower() in ("quit", "exit", "q"):
#         break
#     if question:
#         ask(question)
