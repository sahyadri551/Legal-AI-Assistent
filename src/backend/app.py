"""FastAPI application for end-to-end legal QA."""
from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import asdict
from io import BytesIO
import logging
import os
import threading

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from pypdf.errors import FileNotDecryptedError, PdfReadError

from ingestion.chunking import chunk_text
from retrieval.bm25 import BM25Index
from retrieval.rrf import RRFResult

from pydantic import BaseModel, Field

from backend.qa import HybridQAService
from generation.groq import GroqConfigurationError, GroqGenerator, GroqRateLimitError

logger = logging.getLogger(__name__)


class QARequest(BaseModel):
    query: str = Field(min_length=1)
    history: list[dict[str, str]] = Field(default_factory=list, max_length=12)


class QAResponse(BaseModel):
    answer: str
    model: str
    citations: list[str]
    retrieved_chunks: list[dict]


class SearchResponse(BaseModel):
    query: str
    results: list[dict]


def create_app(service: HybridQAService | None = None, generator: GroqGenerator | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app.state.service is None and generator is None:
            app.state.service = HybridQAService()
        yield

    app = FastAPI(title="Indian Legal Research Assistant", version="0.1.0", lifespan=lifespan)

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
    app.state.service_init_lock = threading.Lock()

    def get_service():
        if app.state.service is not None:
            return app.state.service
        with app.state.service_init_lock:
            if app.state.service is None:
                app.state.service = HybridQAService()
            return app.state.service

    def contextual_query(query, history):
        turns = []
        for turn in history[-8:]:
            role = turn.get("role", "")
            content = (turn.get("text") or turn.get("query") or "").strip()
            if role in {"user", "assistant"} and content:
                turns.append(role + ": " + content[:1200])
        return query if not turns else "Recent conversation:\n" + "\n".join(turns) + "\nCurrent question: " + query

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/search", response_model=SearchResponse)
    def search(request: QARequest) -> SearchResponse:
        try:
            current = get_service()
            results = current.retrieve(contextual_query(request.query, request.history), top_k=20)
        except GroqConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except FileNotFoundError:
            logger.exception("Search indexes unavailable")
            raise HTTPException(status_code=503, detail="Retrieval indexes are unavailable.") from None
        except Exception:
            logger.exception("Search failed")
            raise HTTPException(status_code=502, detail="Search failed due to an internal error.") from None
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
        data = file.file.read(int(float(os.getenv("DOCUMENT_MAX_MB", "15")) * 1024 * 1024) + 1)
        if not data:
            raise HTTPException(status_code=400, detail="The uploaded PDF is empty.")
        if len(data) > int(float(os.getenv("DOCUMENT_MAX_MB", "15")) * 1024 * 1024):
            raise HTTPException(status_code=413, detail="PDF exceeds the configured upload limit.")
        if not data.startswith(b"%PDF-"):
            raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF.")
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
            if getattr(reader, "is_encrypted", False) and not reader.decrypt(""):
                raise HTTPException(status_code=400, detail="Password-protected PDFs are not supported.")
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
            legal_service = app.state.service
            if legal_service is not None:
                try:
                    statute_hits = [hit for hit in legal_service.retrieve(query, top_k=20) if str(hit.metadata.get("doc_type", "")).lower() == "statute"][:4]
                    known_ids = {hit.chunk_id for hit in fused}
                    fused.extend(hit for hit in statute_hits if hit.chunk_id not in known_ids)
                except Exception:
                    logger.exception("Could not retrieve statute context for PDF analysis")
            current_generator = app.state.document_generator
            if current_generator is None:
                current_generator = GroqGenerator()
                app.state.document_generator = current_generator
            if len(records) > 8 and any(term in query.lower() for term in ("summarize", "summarise", "summary", "overview", "key points")):
                from generation.groq import GenerationResult
                summaries, citations = [], []
                for start in range(0, len(records), 8):
                    batch = []
                    for rank, record in enumerate(records[start:start + 8], 1):
                        metadata = {k: v for k, v in record.items() if k not in {"chunk_id", "doc_id", "text"}}
                        batch.append(RRFResult(record["chunk_id"], record["doc_id"], record["text"], 1.0 / (60 + rank), rank, None, metadata))
                    part = current_generator.generate("Summarize the key facts, issues, and conclusions in this section. Cite only the supplied source identifiers.", batch)
                    summaries.append(part.answer)
                    citations.extend(part.citations)
                generation = GenerationResult("\n\n".join(summaries), getattr(current_generator, "model", "Groq"), list(dict.fromkeys(citations)))
            else:
                generation = current_generator.generate(query, fused)
        except (PdfReadError, FileNotDecryptedError) as exc:
            raise HTTPException(status_code=400, detail="The PDF is damaged, unreadable, or password-protected.") from exc
        except HTTPException:
            raise
        except GroqConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
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
            current = get_service()
            result = current.answer(contextual_query(request.query, request.history))
        except GroqConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=503, detail="Retrieval indexes are unavailable.") from exc
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
