"""Streamlit workspace views for document analysis and case-law search."""
from __future__ import annotations

import html
from typing import Any

import streamlit as st

from frontend.client import BackendError, LegalQAClient
from frontend.formatting import esc, first_line, prepare_answer, shorten, source_label


def _render_sources(results: list[dict[str, Any]], title: str) -> None:
    st.markdown(
        f'<div class="top-title" style="margin-bottom:6px">{esc(title)}</div>',
        unsafe_allow_html=True,
    )
    for index, item in enumerate(results, 1):
        metadata = item.get("metadata") or {}
        chunk_id = str(item.get("chunk_id", ""))
        caption = first_line(metadata.get("caption_text"))
        pdf = metadata.get("pdf_filename") or metadata.get("source_pdf") or ""
        rank = item.get("rank", item.get("rrf_rank"))
        score = item.get("score")
        meta_parts = [
            "Judgment",
            str(pdf) if pdf else "",
            f"rank {rank}" if rank is not None else "",
            f"score {float(score):.4f}" if isinstance(score, (int, float)) else "",
        ]
        subtitle = " · ".join(x for x in meta_parts if x)
        st.markdown(
            f"""
            <div style="padding:14px 16px;margin:8px 0;border:1px solid var(--border);
                        border-radius:12px;background:var(--surface);">
              <div style="font-weight:600;color:var(--text);">{index}. {esc(source_label(chunk_id))}</div>
              <div style="font-size:12px;color:var(--muted);margin-top:3px;">{esc(subtitle)}</div>
              {f'<div style="font-size:12px;color:var(--muted);margin-top:4px;">{esc(caption)}</div>' if caption else ''}
              <div style="font:13px/1.65 Merriweather,Georgia,serif;color:var(--body);margin-top:9px;">
                “{esc(shorten(str(item.get("text", ""))))}”
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_document_analysis(client: LegalQAClient) -> None:
    st.markdown(
        '<div class="top-title">Document Analysis</div>'
        '<div class="top-sub">Upload a legal PDF and analyze its contents without adding it to the corpus.</div>',
        unsafe_allow_html=True,
    )
    st.write("")
    uploaded = st.file_uploader(
        "Upload a PDF",
        type=["pdf"],
        accept_multiple_files=False,
        key="analysis_pdf",
        help="The document is processed for this analysis only; it is not added to the indexed corpus.",
    )
    instruction = st.text_area(
        "Analysis instruction",
        value="Summarize the document, identify the principal legal issues, important provisions or holdings, and flag material uncertainties. Ground every material point in the uploaded document.",
        height=120,
        key="analysis_instruction",
    )

    if uploaded is not None:
        st.caption(f"{uploaded.name} · {len(uploaded.getvalue()) / 1024 / 1024:.2f} MB")

    if st.button(
        ":material/analytics: Analyze document",
        key="run_document_analysis",
        type="primary",
        disabled=uploaded is None,
        use_container_width=False,
    ):
        try:
            with st.spinner("Extracting the document and generating a grounded analysis..."):
                result = client.analyze_document(
                    uploaded.name,
                    uploaded.getvalue(),
                    instruction,
                )
            st.session_state.document_analysis_result = result
        except (BackendError, ValueError) as exc:
            st.error(str(exc))

    result = st.session_state.get("document_analysis_result")
    if result:
        st.divider()
        st.markdown(
            f'<div style="font-size:12px;color:var(--muted);margin-bottom:8px;">'
            f'{esc(result["filename"])} · {result["pages"]} pages · {result["model"]}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            prepare_answer(result["answer"], True),
            unsafe_allow_html=True,
        )
        sources = result.get("sources", [])
        if sources:
            st.divider()
            _render_sources(sources, "Document evidence")


def render_case_law_search(client: LegalQAClient) -> None:
    st.markdown(
        '<div class="top-title">Case Law Search</div>'
        '<div class="top-sub">Search the indexed Supreme Court judgment corpus using the same hybrid BM25 + dense RRF retrieval stack.</div>',
        unsafe_allow_html=True,
    )
    st.write("")
    query = st.text_input(
        "Search judgments",
        placeholder="e.g. anticipatory bail section 438",
        key="case_law_query",
    )
    col1, col2 = st.columns([1, 4])
    with col1:
        top_k = st.number_input("Results", min_value=1, max_value=20, value=8, step=1)
    with col2:
        st.write("")
        search = st.button(
            ":material/search: Search case law",
            key="run_case_law_search",
            type="primary",
        )

    if search:
        if not query.strip():
            st.error("Enter a case-law search query.")
        else:
            try:
                with st.spinner("Searching BM25 + dense indexes and fusing the rankings..."):
                    results = client.search_case_law(query, int(top_k))
                st.session_state.case_law_results = results
                st.session_state.case_law_last_query = query.strip()
            except (BackendError, ValueError) as exc:
                st.error(str(exc))

    results = st.session_state.get("case_law_results", [])
    if results:
        st.divider()
        st.caption(
            f'{len(results)} judgment results for “{st.session_state.get("case_law_last_query", "")}”'
        )
        _render_sources(results, "Ranked judgments")
    elif st.session_state.get("case_law_last_query"):
        st.info("No matching judgments were found in the local corpus.")
