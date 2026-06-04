import streamlit as st
from database.db_manager import (
    init_db,
    get_sessions,
    create_session,
    get_session_by_document,
    save_message,
    get_chat_history,
)
from services.groq_service import get_stream, parse_stream_chunks

st.set_page_config(page_title="Document Chat", layout="wide")
init_db()

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

if "active_document_id" not in st.session_state:
    st.session_state.active_document_id = None


def open_document_chat(document_id):
    if not document_id:
        return

    if st.session_state.active_document_id == document_id:
        return

    st.session_state.active_document_id = document_id

    existing_session = get_session_by_document(document_id)
    if existing_session:
        st.session_state.current_session_id = existing_session[0]
    else:
        st.session_state.current_session_id = create_session(document_id=document_id)


with st.sidebar:
    st.title("Chat History")

    # Example: call this after upload completes successfully
    # if uploaded_document_id:
    #     open_document_chat(uploaded_document_id)

    # Example: call this when a recent document is selected
    # if recent_document_id:
    #     open_document_chat(recent_document_id)

    st.divider()

    sessions = get_sessions()
    for s_id, s_title, s_document_id in sessions:
        label = f"{s_title} [{s_document_id}]"
        if st.button(label, key=f"session_{s_id}", use_container_width=True):
            st.session_state.current_session_id = s_id
            st.session_state.active_document_id = s_document_id
            st.rerun()

st.title("Document Chat")

if st.session_state.active_document_id is None:
    st.info("Upload a document or select one from recently uploaded to start chatting.")
elif st.session_state.current_session_id is None:
    st.info("No chat session found for the selected document.")
else:
    chat_history = get_chat_history(st.session_state.current_session_id)

    for message in chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about this document"):
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