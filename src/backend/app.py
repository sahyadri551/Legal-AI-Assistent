"""FastAPI application for end-to-end legal QA."""
from __future__ import annotations

from dataclasses import asdict
from io import BytesIO
import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader

from ingestion.chunking import chunk_text
from retrieval.bm25 import BM25Index
from retrieval.rrf import RRFResult

from pydantic import BaseModel, Field

from backend.qa import HybridQAService
from generation.groq import GroqGenerator, GroqRateLimitError


class QARequest(BaseModel):
    query: str = Field(min_length=1)


class QAResponse(BaseModel):
    answer: str
    model: str
    citations: list[str]
    retrieved_chunks: list[dict]


class SearchResponse(BaseModel):
    query: str
    results: list[dict]


def create_app(service: HybridQAService | None = None, generator: GroqGenerator | None = None) -> FastAPI:
    app = FastAPI(title="Indian Legal Research Assistant", version="0.1.0")

    configured_origins = [
        origin.strip()
        for origin in os.getenv("FRONTEND_ORIGINS", "").split(",")
        if origin.strip()
    ]
    if not configured_origins:
        configured_origins = [
            "http://localhost:8501",
            "http://127.0.0.1:8501",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=configured_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.service = service
    app.state.document_generator = generator

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/search", response_model=SearchResponse)
    def search(request: QARequest) -> SearchResponse:
        try:
            current = app.state.service
            if current is None:
                current = HybridQAService()
                app.state.service = current
            results = current.retrieve(request.query, top_k=20)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=503, detail=f"Retrieval indexes are unavailable: {exc}") from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Search failed: {type(exc).__name__}: {exc}") from exc
        return SearchResponse(
            query=request.query,
            results=[asdict(result) for result in results],
        )

    @app.post("/document-analysis", response_model=QAResponse)
    def document_analysis(
        file: UploadFile = File(...),
        query: str = Form(...),
    ) -> QAResponse:
        if not query.strip():
            raise HTTPException(status_code=400, detail="query must not be empty")
        filename = file.filename or "uploaded-document.pdf"
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF documents are supported.")
        data = file.file.read()
        if not data:
            raise HTTPException(status_code=400, detail="The uploaded PDF is empty.")
        try:
            max_upload_mb = float(os.getenv("DOCUMENT_MAX_MB", "15"))
        except ValueError as exc:
            raise HTTPException(status_code=500, detail="DOCUMENT_MAX_MB must be numeric.") from exc
        if max_upload_mb <= 0:
            raise HTTPException(status_code=500, detail="DOCUMENT_MAX_MB must be greater than zero.")
        max_upload_bytes = int(max_upload_mb * 1024 * 1024)
        if len(data) > max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"PDF is too large. Maximum size is {max_upload_mb:g} MB.",
            )
        try:
            reader = PdfReader(BytesIO(data))
            pages = [(page.extract_text() or "").strip() for page in reader.pages]
            text = "\n\n".join(page for page in pages if page)
            chunks = chunk_text(text, max_chars=1200, overlap_chars=150)
            if not chunks:
                raise ValueError("No extractable text was found in the PDF.")
            records = [
                {
                    "chunk_id": f"upload:{index}",
                    "doc_id": "uploaded-document",
                    "text": chunk,
                    "doc_type": "uploaded_pdf",
                    "pdf_filename": filename,
                    "chunk_index": index,
                }
                for index, chunk in enumerate(chunks)
            ]
            index = BM25Index.build(records)
            bm25_results = index.search(query, top_k=8)
            fused = [
                RRFResult(
                    chunk_id=result.chunk_id,
                    doc_id=result.doc_id,
                    text=result.text,
                    score=1.0 / (60 + result.rank),
                    bm25_rank=result.rank,
                    dense_rank=None,
                    metadata=result.metadata,
                )
                for result in bm25_results
            ]
            current_generator = app.state.document_generator
            if current_generator is None:
                current_generator = GroqGenerator()
                app.state.document_generator = current_generator
            generation = current_generator.generate(query, fused)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except TimeoutError as exc:
            raise HTTPException(status_code=504, detail=str(exc)) from exc
        except GroqRateLimitError as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        return QAResponse(
            answer=generation.answer,
            model=generation.model,
            citations=generation.citations,
            retrieved_chunks=[asdict(chunk) for chunk in fused],
        )

    @app.post("/qa", response_model=QAResponse)
    def qa(request: QARequest) -> QAResponse:
        try:
            current = app.state.service
            if current is None:
                current = HybridQAService()
                app.state.service = current
            result = current.answer(request.query)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=503, detail=f"Retrieval indexes are unavailable: {exc}") from exc
        except TimeoutError as exc:
            raise HTTPException(status_code=504, detail=str(exc)) from exc
        except GroqRateLimitError as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        return QAResponse(
            answer=result.generation.answer,
            model=result.generation.model,
            citations=result.generation.citations,
            retrieved_chunks=[asdict(chunk) for chunk in result.retrieved],
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)
