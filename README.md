# Document Analyzer QnA

Streamlit-based document chat app for uploading PDFs, indexing them into Chroma, and asking questions against a single selected document with Groq-powered responses.

## Features

- Upload a PDF and index it into Chroma for retrieval-augmented Q&A.
- Deduplicate documents by file hash so the same file is only stored once.
- Create multiple chat sessions for the same document.
- Group chat history by document in the sidebar.
- Delete a document from storage while keeping old chats visible as unavailable.
- Remove stale chats for deleted documents from the sidebar.
- Stream assistant responses in the chat UI.

## How It Works

The app keeps three layers in sync:

- `documents` in SQLite
  Stores one row per unique uploaded file.
- `sessions` in SQLite
  Stores chat sessions, each linked to one document.
- `document_chunks` in Chroma
  Stores embedded PDF chunks with `document_id` metadata so retrieval stays scoped to the active document.

When a PDF is uploaded:

1. Its bytes are hashed.
2. SQLite checks whether that file already exists.
3. If it is new, the PDF is parsed, chunked, embedded, and stored in Chroma.
4. A new chat session is created for that document.

When a user asks a question:

1. The active document ID is read from the current session.
2. Chroma retrieves only chunks for that document.
3. The retrieved context and chat history are sent to Groq.
4. The response is streamed back into Streamlit and saved to SQLite.

## Tech Stack

- `Streamlit` for the UI
- `SQLite` for document/session/message storage
- `Chroma` for vector storage
- `LangChain` components for loading, splitting, and retrieval
- `sentence-transformers/all-MiniLM-L6-v2` for embeddings
- `Groq` for answer generation
- `pypdf` / `PyPDFLoader` for PDF ingestion

## Project Structure

```text
.
|-- app.py
|-- config.py
|-- requirements.txt
|-- database/
|   |-- db_manager.py
|   `-- sqlite.py
|-- services/
|   `-- groq_service.py
`-- utils/
    |-- embed.py
    |-- parse.py
    |-- prompts.py
    `-- retrieve.py
```

## Requirements

- Python 3.10+ recommended
- A Groq API key

## Installation

1. Create and activate a virtual environment.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Create a `.env` file in the project root.

```env
GROQ_API_KEY=your_groq_api_key
CHROMA_DIR=./chroma_rag_demo
COLLECTION_NAME=document_chunks
DB_NAME=history.db
```

## Configuration

[config.py]() reads these environment variables:

- `GROQ_API_KEY`
- `CHROMA_DIR`
- `COLLECTION_NAME`
- `DB_NAME`

If `GROQ_API_KEY` is missing, the app exits at startup.

## Run the App

```powershell
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal.

## Usage

1. Upload a PDF from the sidebar.
2. Wait for the parsing/indexing spinner to finish.
3. Open the document’s grouped chat section in the sidebar.
4. Start chatting with that document.
5. Use the `⋮` menu next to a document name to:
   - start a new chat
   - delete the document
   - remove stale chats for deleted documents

## Current Behavior

- Uploading the same PDF again reuses the existing stored document.
- A document can have multiple chat sessions.
- Sessions are grouped by document in the sidebar.
- If a document is deleted from Chroma and SQLite, its old chats become unavailable.
- Unavailable chat groups can be removed separately.
- Delete actions show loading spinners and temporarily block other sidebar actions.

## Known Limitations

- PDF extraction quality depends on the source file. Repeated headers, table-of-contents pages, or messy layouts can lead to noisy retrieval.
- Broad questions like “what is this about?” may perform worse when the retrieved chunks are mostly outlines instead of body text.
- The app currently supports PDF upload only.
- Retrieval quality depends on chunking, embedding quality, and the cleanliness of extracted PDF text.

## Troubleshooting

### `GROQ_API_KEY not found`

Set the key in `.env` or your shell environment before starting the app.

### Deleted document chats still appear

That is expected until you remove those stale chats from the deleted document’s menu.

### Weak or repetitive answers

This usually means the retrieved PDF text is repetitive or poorly extracted. Try:

- asking a more specific question
- uploading a cleaner PDF

