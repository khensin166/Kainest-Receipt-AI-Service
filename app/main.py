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
)

# CORS — izinkan frontend Kainest dan development lokal
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ganti dengan domain spesifik di production
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
