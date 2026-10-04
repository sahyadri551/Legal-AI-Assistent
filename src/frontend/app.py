"""Streamlit UI for the Indian Legal Research Assistant."""
from __future__ import annotations

import os

import streamlit as st

from frontend.client import BackendError, LegalQAClient

st.set_page_config(
    page_title="Indian Legal Research Assistant",
    page_icon="⚖️",
    layout="wide",
)

st.title("Indian Legal Research Assistant")
st.caption("Hybrid BM25 + dense retrieval with grounded Ollama generation.")

with st.sidebar:
    st.header("Connection")
    api_url = st.text_input(
        "Backend URL",
        value=os.getenv("BACKEND_URL", "http://127.0.0.1:8000"),
    )
    st.caption("Start FastAPI before using the assistant.")

client = LegalQAClient(api_url)

try:
    if client.health():
        st.success("Backend connected")
except BackendError as exc:
    st.error(str(exc))

query = st.text_area(
    "Legal question",
    placeholder="Example: What are the powers of the High Court regarding bail?",
    height=120,
)

if st.button("Ask", type="primary", use_container_width=True):
    if not query.strip():
        st.warning("Please enter a legal question.")
    else:
        with st.spinner("Searching the legal corpus and generating an answer..."):
            try:
                result = client.ask(query)
            except (BackendError, ValueError) as exc:
                st.error(str(exc))
            else:
                st.subheader("Answer")
                st.markdown(result.answer)

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Model", result.model)
                with col2:
                    st.metric("Citations", len(result.citations))

                if result.citations:
                    st.subheader("Citations")
                    for citation in result.citations:
                        st.code(citation)

                if result.retrieved_chunks:
                    st.subheader("Retrieved sources")
                    for index, chunk in enumerate(result.retrieved_chunks, start=1):
                        title = f"{index}. {chunk.get('chunk_id', 'Unknown source')}"
                        with st.expander(title):
                            st.write(chunk.get("text", ""))
                            metadata = chunk.get("metadata") or {}
                            if metadata:
                                st.json(metadata)
