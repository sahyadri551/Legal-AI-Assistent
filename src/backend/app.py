"""FastAPI application for end-to-end legal QA."""
from __future__ import annotations

from dataclasses import asdict
import base64

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.qa import HybridQAService
from backend.workspaces import WorkspaceService
from generation.groq import GroqRateLimitError


class QARequest(BaseModel):
    query: str = Field(min_length=1)


class QAResponse(BaseModel):
    answer: str
    model: str
    citations: list[str]
    retrieved_chunks: list[dict]


class CaseLawSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=8, ge=1, le=20)


class CaseLawSearchResponse(BaseModel):
    results: list[dict]


class DocumentAnalysisRequest(BaseModel):
    filename: str = Field(min_length=1)
    content_base64: str = Field(min_length=1)
    instruction: str = Field(min_length=1)


class DocumentAnalysisResponse(BaseModel):
    filename: str
    pages: int
    model: str
    answer: str
    citations: list[str]
    sources: list[dict]


def create_app(service: HybridQAService | None = None) -> FastAPI:
    app = FastAPI(title="Indian Legal Research Assistant", version="0.1.0")
    app.state.service = service
    app.state.workspace = None

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

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


    @app.post("/case-law/search", response_model=CaseLawSearchResponse)
    def case_law_search(request: CaseLawSearchRequest) -> CaseLawSearchResponse:
        try:
            workspace = app.state.workspace
            if workspace is None:
                workspace = WorkspaceService()
                app.state.workspace = workspace
            return CaseLawSearchResponse(results=workspace.search_case_law(request.query, request.top_k))
        except FileNotFoundError as exc:
            raise HTTPException(status_code=503, detail=f"Retrieval indexes are unavailable: {exc}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/document-analysis", response_model=DocumentAnalysisResponse)
    def document_analysis(request: DocumentAnalysisRequest) -> DocumentAnalysisResponse:
        try:
            raw = base64.b64decode(request.content_base64, validate=True)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=400, detail="Invalid base64 document payload.") from exc
        try:
            workspace = app.state.workspace
            if workspace is None:
                workspace = WorkspaceService()
                app.state.workspace = workspace
            result = workspace.analyze_document(request.filename, raw, request.instruction)
            return DocumentAnalysisResponse(**result)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=503, detail=f"Retrieval indexes are unavailable: {exc}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except TimeoutError as exc:
            raise HTTPException(status_code=504, detail=str(exc)) from exc
        except GroqRateLimitError as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)
