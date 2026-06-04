from config import api_key
import os
from groq import Groq
from utils.parse import get_dynamic_top_k
from database.db_manager import get_vector_store
from utils.prompts import RAG_QA_PROMPT as SYSTEM_PROMPT

groq_client = Groq(api_key=os.environ.get(api_key))

def get_stream(chat_history, fresh_prompt, document_id):
    topk = get_dynamic_top_k(fresh_prompt)

    retriever = get_vector_store().as_retriever(
        search_kwargs={"k": topk, "filter": {"document_id": str(document_id)}}
    )
    context = retriever.invoke(fresh_prompt)

    # context = retrieve.format_context(docs)
    prompt = f"""Conversation history:
                {chat_history}

                Latest user question:
                {fresh_prompt}

                Retrieved context:
                {context}

               Rules:
                - Use ONLY the document context.
                - Do NOT copy the document context directly.
                - Do NOT include raw source labels.
                - Do NOT include file paths.
                - Do NOT include lines like [Source 1 | ...].
                - Do NOT include metadata.
                - Only write the final answer.
                - If useful, mention page numbers naturally, like "on page 6".
                - Do not repeat the context. Write only the final answer.
                - If the answer is not in the context, say exactly:
                "I could not find that information in the provided document."""

    return groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        stream=True,
    )

def parse_stream_chunks(raw_stream):
    for chunk in raw_stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content
