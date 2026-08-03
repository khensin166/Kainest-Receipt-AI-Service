"""
RapidOCR Service — Fast CPU-based OCR using ONNX Runtime.

RapidOCR menggunakan PaddleOCR models yang dikonversi ke ONNX,
dieksekusi melalui ONNX Runtime (C++) tanpa membutuhkan GPU / CUDA.
Kecepatan: ~1-3 detik per gambar struk pada CPU biasa.

Docs: https://github.com/RapidAI/RapidOCR
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from app.core.constants import MIN_OCR_CONFIDENCE
from app.core.logger import logger

# ─── Lazy Singleton ──────────────────────────────────────────────────────────
_rapid_ocr = None


def _get_engine():
    global _rapid_ocr
    if _rapid_ocr is None:
        logger.info("[RapidOCR] Memuat RapidOCR ONNX Engine...")
        from rapidocr_onnxruntime import RapidOCR
        _rapid_ocr = RapidOCR()
        logger.info("[RapidOCR] Engine berhasil dimuat.")
    return _rapid_ocr


# ─── Data Classes ────────────────────────────────────────────────────────────
from dataclasses import dataclass


@dataclass
class OCRLine:
    text: str
    bbox: list[int]   # [x_min, y_min, x_max, y_max]
    confidence: float


@dataclass
class OCRResult:
    lines: list[OCRLine]
    avg_confidence: float
    raw_text: str


# ─── Run OCR ─────────────────────────────────────────────────────────────────

def run_rapidocr(pil_image: Image.Image) -> OCRResult:
    """
    Jalankan RapidOCR (ONNX) pada gambar PIL.
    Return OCRResult berisi list baris teks beserta confidence score-nya.
    """
    engine = _get_engine()

    # Konversi PIL -> numpy array (RGB)
    np_image = np.array(pil_image.convert("RGB"))

    logger.info("[RapidOCR] Menjalankan OCR pada gambar...")
    result, elapse = engine(np_image, return_word_box=False)
    
    # elapse adalah list time untuk [det, cls, rec]
    total_time = sum(elapse) if isinstance(elapse, list) else float(elapse)
    logger.info(f"[RapidOCR] OCR selesai dalam {total_time:.2f} detik.")

    lines: list[OCRLine] = []

    if result is None:
        logger.warning("[RapidOCR] Tidak ada teks yang terdeteksi.")
        return OCRResult(lines=[], avg_confidence=0.0, raw_text="")

    for item in result:
        # RapidOCR result format: [bbox_points, text, confidence]
        bbox_pts, text, conf = item[0], item[1], float(item[2])

        # Konversi polygon bbox -> [x_min, y_min, x_max, y_max]
        xs = [p[0] for p in bbox_pts]
        ys = [p[1] for p in bbox_pts]
        bbox = [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]

        text = str(text).strip()
        if not text:
            continue

        if conf < MIN_OCR_CONFIDENCE:
            logger.debug(f"[RapidOCR] Skip baris confidence rendah ({conf:.2f}): {text!r}")
            continue

        lines.append(OCRLine(text=text, bbox=bbox, confidence=conf))

    avg_conf = sum(ln.confidence for ln in lines) / len(lines) if lines else 0.0
    raw_text = "\n".join(ln.text for ln in lines)

    logger.info(
        f"[RapidOCR] Ekstraksi selesai: {len(lines)} baris, "
        f"avg confidence={avg_conf:.3f}"
    )
    return OCRResult(lines=lines, avg_confidence=avg_conf, raw_text=raw_text)
