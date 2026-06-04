import config
from groq import Groq

def main() :

    client = Groq(api_key=config.api_key)

    system_prompt = (
            "You are a database-integrated text processing utility. Analyze the user text data. "
            "You MUST output your response in a strict formatted style containing two sections:\n"
            "1. A bulleted summary synthesized from the reviews.\n"
            "Keep your response analytical and professional."
        )

    response = client.chat.completions.create(
    model="llama-3.1-8b-instant",        # Fast, free model on Groq
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Explain RAG in one sentence."}
    ],
    temperature=0.,
    )

    print("✅ Groq connection successful!")
    print("-" * 40)
    print(response.choices[0].message.content)

if __name__ == "__main__" :
    main()