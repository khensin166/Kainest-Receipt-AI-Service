"""
OCR Service — Kainest Receipt AI Service

Menggunakan RapidOCR (ONNX Runtime) — cepat, ~1-3 detik, CPU-only.
Mengekspor dataclass OCRLine dan OCRResult serta fungsi run_ocr()
agar semua consumer tidak perlu berubah.
"""

from __future__ import annotations

from PIL import Image

from app.core.logger import logger

# Re-export data classes supaya consumer bisa import dari sini
from app.services.rapidocr_service import OCRLine, OCRResult, _get_engine, run_rapidocr


def warmup_ocr():
    """
    Pre-load engine OCR saat startup agar request pertama tidak lambat.
    Dipanggil dari main.py lifespan.
    """
    _get_engine()
    logger.info("[OCRService] Engine RapidOCR berhasil di-warmup.")


def run_ocr(pil_image: Image.Image) -> OCRResult:
    """
    Public API — Ekstrak teks dari gambar.
    Return OCRResult.
    """
    logger.info("[OCRService] Menjalankan OCR...")
    return run_rapidocr(pil_image)
