from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from phase10_multilingual.src.api.routes import router
from phase10_multilingual.src.config.settings import settings

app = FastAPI(
    title="LegalAId - Phase 10 Multilingual API",
    description="Multilingual RAG layer for handling English, Hindi, and Hinglish inputs securely.",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/language", tags=["Language Processing"])

# Mount static frontend web UI
static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=FileResponse)
    def read_root():
        return FileResponse(str(static_dir / "index.html"))
else:
    @app.get("/")
    def read_root_fallback():
        return {"message": "LegalAId Phase 10 Multilingual API is running. Check /docs for documentation."}

if __name__ == "__main__":
    uvicorn.run("phase10_multilingual.src.main:app", host=settings.host, port=settings.port, reload=settings.debug)
