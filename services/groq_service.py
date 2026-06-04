from config import api_key
from groq import Groq
import os
import utils.retrieve as retrieve

groq_client = Groq(api_key=os.environ.get(api_key))

def get_stream(model_name, conversation_history, fresh_prompt):

    topk = retrieve.get_dynamic_top_k(fresh_prompt)

    retriever = retrieve.vector_store.as_retriever(
        search_kwargs={"k": topk}
    )
    docs = retriever.invoke(fresh_prompt)


    # Step 6: Generate
    context = retrieve.format_context(docs)
    prompt = f"""Conversation history:
                {conversation_history}

                Latest user question:
                {fresh_prompt}

                Retrieved context:
                {context}

                Answer using ONLY the context above. Include page references."""

    return groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": retrieve.SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.5,
        stream = True,
    )

def parse_stream_chunks(raw_stream):

    for chunk in raw_stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content