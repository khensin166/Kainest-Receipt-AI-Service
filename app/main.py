"""
Entry point — Kainest Receipt AI Service
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import health, receipt, split
from app.core.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load OCR engine saat startup agar request pertama tidak lambat."""
    logger.info("🚀 Kainest Receipt AI Service sedang starting up... (Engine: RAPIDOCR)")
    try:
        from app.services.ocr_service import warmup_ocr
        warmup_ocr()
        logger.info("✅ OCR Engine 'RAPIDOCR' berhasil dimuat.")
    except Exception as e:
        logger.warning(f"⚠️ Gagal pre-load OCR engine: {e}. Model akan dimuat pada request pertama.")
    yield
    logger.info("👋 Service shutdown.")


app = FastAPI(
    title="Kainest Receipt AI Service",
    description=(
        "## 🧾 Kainest Receipt AI Service & Split Bill Engine\n\n"
        "- **Scan & Extract** foto struk belanja menggunakan RapidOCR (ONNX) + Groq LLM\n"
        "- **Split Bill** (Itemized atau Bagi Rata) dengan alokasi pajak proporsional\n\n"
        "Dokumentasi alur lengkap tersedia di `AGENTS.md` dan `docs/flow_diagram.png`."
    ),
    version="1.0.0",
    contact={"name": "Kainest Team", "url": "https://kainest.kenantomfie.com"},
    lifespan=lifespan,
    docs_url=None,     # Disable default docs
    redoc_url=None,    # Disable default redoc
    openapi_url=None,  # Disable default openapi.json
)

# CORS — izinkan frontend Kainest dan development lokal
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://kainest.kenantomfie.com",
        "https://staging.kainest.kenantomfie.com",
        "http://localhost",
        "http://localhost:5173", # untuk vue dev
        "http://localhost:3000",
        "https://staging.kainest-be.v.kenantomfie.com",
        "https://kainest-be.v.kenantomfie.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"code": 500, "status": "error", "message": "Terjadi kesalahan internal pada server."},
    )


# Mount routers
app.include_router(health.router)
app.include_router(receipt.router)
app.include_router(split.router)


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Kainest Receipt AI Service", "docs": "/docs", "health": "/health"}


# --- Protected Swagger Documentation ---
from fastapi import Depends
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from app.core.security import verify_docs_auth

@app.get("/docs", include_in_schema=False)
async def get_swagger_documentation(username: str = Depends(verify_docs_auth)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title=f"{app.title} - Swagger UI")

@app.get("/redoc", include_in_schema=False)
async def get_redoc_documentation(username: str = Depends(verify_docs_auth)):
    return get_redoc_html(openapi_url="/openapi.json", title=f"{app.title} - ReDoc")

@app.get("/openapi.json", include_in_schema=False)
async def openapi(username: str = Depends(verify_docs_auth)):
    return get_openapi(title=app.title, version=app.version, routes=app.routes)
