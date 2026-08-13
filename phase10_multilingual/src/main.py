import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router
from src.config.settings import settings

app = FastAPI(
    title="LegalAId - Phase 10 Multilingual API",
    description="Multilingual layer for handling English, Hindi, and Hinglish inputs securely.",
    version="1.0.0"
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

@app.get("/")
def read_root():
    return {"message": "LegalAId Phase 10 Multilingual API is running. Check /docs for documentation."}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host=settings.host, port=settings.port, reload=settings.debug)
