# Section 1 — Project Title and Description

## Document Analyzer QnA

Document Analyzer QnA is a Streamlit application that lets users upload PDF or TXT documents, index them with Chroma, and ask questions about one document at a time using the Groq API. It is for students, developers, and anyone who wants a simple document-based AI chat tool.

# Section 2 — Problem Statement

Reading long documents and manually searching for answers can be slow and frustrating, especially when users want quick summaries or fact lookup. This application solves that problem by turning uploaded documents into searchable chat sessions, making it easier to explore the contents through natural-language questions.

# Section 3 — Technology Stack

- Python
- Streamlit
- SQLite
- LangChain
- langchain-chroma
- langchain-huggingface
- pypdf
- python-dotenv
- Groq API

# Section 4 — Setup Instructions

1. Clone the repository.

```powershell
git clone <your-repository-url>
cd document_analyzer_qna
```

2. Create and activate a virtual environment.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Install dependencies.

```powershell
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and fill in your values.

```env
GROQ_API_KEY=your_groq_api_key
CHROMA_DIR=./db
COLLECTION_NAME=document_chunks
DB_NAME=history.db
```

5. Run the application.

```powershell
streamlit run app.py
```

# Section 5 — Usage Examples

## Example 1

User input:

```text
What is this document about?
```

Application output:

```text
This document is mainly about the project goals, requirements, system design, implementation, testing, and deployment. It reads like a project report or technical overview with sections covering both planning and code structure.
```

## Example 2

User input:

```text
What are the main points on page 2?
```

Application output:

```text
The document says the main points include identifying key requirements, developing a system design, implementing a working prototype, testing and refining the system, and deploying the final product.
```

# Section 6 — Known Limitations

- PDF extraction can be noisy when a file has repeated headers, outlines, or poor formatting, which can lead to repetitive or weak answers.
- Broad questions such as “what is this about?” or ambiguous questions such as “what is the first point?” may return less accurate answers if the retrieved chunks are unclear.

# Section 7 — Future Improvements

- Improve preprocessing and chunk cleanup so repeated PDF text and outline-heavy pages do not dominate retrieval.
- Add stronger answer controls for summary-style and ambiguous questions, plus better citations and document previews.
