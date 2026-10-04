"""FastAPI application for end-to-end legal QA."""
from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.qa import HybridQAService
from generation.groq import GroqRateLimitError


class QARequest(BaseModel):
    query: str = Field(min_length=1)


class QAResponse(BaseModel):
    answer: str
    model: str
    citations: list[str]
    retrieved_chunks: list[dict]


def create_app(service: HybridQAService | None = None) -> FastAPI:
    app = FastAPI(title="Indian Legal Research Assistant", version="0.1.0")
    app.state.service = service

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


    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)
