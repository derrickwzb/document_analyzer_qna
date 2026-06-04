import streamlit as st
from collections import OrderedDict

from database.db_manager import (
    create_session,
    delete_document,
    delete_sessions_for_document,
    get_chat_history,
    get_document,
    get_documents,
    get_or_create_document,
    get_sessions,
    init_db,
    save_message,
)
from services.groq_service import get_stream, parse_stream_chunks
from utils.parse import delete_pdf, index_pdf


st.set_page_config(page_title="Document Chat", layout="wide")
init_db()

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

if "active_document_id" not in st.session_state:
    st.session_state.active_document_id = None

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "pending_delete_document_id" not in st.session_state:
    st.session_state.pending_delete_document_id = None

if "pending_delete_sessions_document_id" not in st.session_state:
    st.session_state.pending_delete_sessions_document_id = None


def start_new_chat_for_document(document_id):
    st.session_state.active_document_id = document_id
    st.session_state.current_session_id = create_session(document_id=document_id)


def handle_uploaded_document(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    document_id, is_new_document = get_or_create_document(uploaded_file.name, file_bytes)

    if is_new_document:
        index_pdf(uploaded_file.name, file_bytes, document_id)

    start_new_chat_for_document(document_id)
    return is_new_document


def handle_deleted_document(document_id):
    delete_pdf(document_id)
    delete_document(document_id)

    if st.session_state.active_document_id == document_id:
        st.session_state.active_document_id = None
        st.session_state.current_session_id = None


def handle_deleted_document_sessions(document_id):
    deleted_count = delete_sessions_for_document(document_id)

    if st.session_state.active_document_id == document_id:
        st.session_state.active_document_id = None
        st.session_state.current_session_id = None

    return deleted_count


with st.sidebar:
    st.title("Documents")

    is_busy = (
        st.session_state.pending_delete_document_id is not None
        or st.session_state.pending_delete_sessions_document_id is not None
    )

    if st.session_state.pending_delete_document_id is not None:
        with st.spinner("Deleting document..."):
            handle_deleted_document(st.session_state.pending_delete_document_id)
        st.session_state.pending_delete_document_id = None
        st.session_state.upload_status = (
            "Document deleted. Existing chats for it are now unavailable."
        )
        st.rerun()

    if st.session_state.pending_delete_sessions_document_id is not None:
        with st.spinner("Removing unavailable chats..."):
            deleted_count = handle_deleted_document_sessions(
                st.session_state.pending_delete_sessions_document_id
            )
        st.session_state.pending_delete_sessions_document_id = None
        st.session_state.upload_status = (
            f"Removed {deleted_count} chat session(s) for the deleted document."
        )
        st.rerun()

    uploaded_file = st.file_uploader(
        "Upload a PDF",
        type=["pdf"],
        key=f"pdf_uploader_{st.session_state.uploader_key}",
        disabled=is_busy,
    )
    if uploaded_file is not None:
        upload_key = (uploaded_file.name, uploaded_file.size)
        if st.session_state.get("last_uploaded_key") != upload_key:
            with st.spinner("Parsing and uploading PDF..."):
                is_new_document = handle_uploaded_document(uploaded_file)
            st.session_state.last_uploaded_key = upload_key
            st.session_state.uploader_key += 1
            st.session_state.upload_status = (
                "Document uploaded and indexed."
                if is_new_document
                else "Document already exists. Reusing the stored copy."
            )
            st.rerun()

    if st.session_state.get("upload_status"):
        st.caption(st.session_state.upload_status)

    st.divider()
    st.title("Chat History")

    documents = {
        document_id: file_name
        for document_id, file_name, _, _ in get_documents()
    }
    sessions = get_sessions()
    grouped_sessions = OrderedDict()
    for s_id, s_title, s_document_id, file_name in sessions:
        resolved_name = documents.get(s_document_id) or file_name
        document_label = resolved_name or f"Deleted document #{s_document_id}"
        if s_document_id not in grouped_sessions:
            grouped_sessions[s_document_id] = {
                "label": document_label,
                "sessions": [],
                "is_deleted": s_document_id not in documents,
            }
        grouped_sessions[s_document_id]["sessions"].append((s_id, s_title))

    for document_id, group in grouped_sessions.items():
        with st.container(border=True):
            title_col, menu_col = st.columns([0.82, 0.18])
            with title_col:
                st.markdown(f"**{group['label']}**")
            with menu_col:
                if is_busy:
                    st.button("⋮", key=f"menu_disabled_{document_id}", disabled=True, use_container_width=True)
                else:
                    with st.popover("⋮", use_container_width=True):
                        if group["is_deleted"]:
                            if st.button(
                                "Remove chats",
                                key=f"delete_group_{document_id}",
                                use_container_width=True,
                            ):
                                st.session_state.pending_delete_sessions_document_id = document_id
                                st.rerun()
                        else:
                            if st.button(
                                "New chat",
                                key=f"new_chat_{document_id}",
                                use_container_width=True,
                            ):
                                start_new_chat_for_document(document_id)
                                st.rerun()
                            if st.button(
                                "Delete document",
                                key=f"delete_document_{document_id}",
                                use_container_width=True,
                            ):
                                st.session_state.pending_delete_document_id = document_id
                                st.rerun()

            with st.expander("Chats", expanded=document_id == st.session_state.active_document_id):
                if group["is_deleted"]:
                    st.caption("This document was deleted. These chats are kept only for reference until removed.")

                for s_id, s_title in group["sessions"]:
                    button_type = "primary" if s_id == st.session_state.current_session_id else "secondary"
                    if st.button(
                        s_title,
                        key=f"session_{s_id}",
                        use_container_width=True,
                        type=button_type,
                        disabled=is_busy,
                    ):
                        st.session_state.current_session_id = s_id
                        st.session_state.active_document_id = document_id
                        st.rerun()


st.title("Document Chat")

if st.session_state.current_session_id is None:
    st.info("Upload a PDF to start a new chat.")
else:
    active_document = get_document(st.session_state.active_document_id)
    chat_history = get_chat_history(st.session_state.current_session_id)

    for message in chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if active_document is None:
        st.warning("This chat is linked to a document that has been deleted, so it can no longer be used.")
    elif prompt := st.chat_input("Ask about this document"):
        with st.chat_message("user"):
            st.markdown(prompt)

        save_message(st.session_state.current_session_id, "user", prompt)

        with st.chat_message("assistant"):
            try:
                raw_stream = get_stream(
                    chat_history=chat_history,
                    fresh_prompt=prompt,
                    document_id=st.session_state.active_document_id,
                )
                clean_text_stream = parse_stream_chunks(raw_stream)
                full_response = st.write_stream(clean_text_stream)
                save_message(st.session_state.current_session_id, "assistant", full_response)
            except Exception as e:
                st.error(f"Error: {str(e)}")
