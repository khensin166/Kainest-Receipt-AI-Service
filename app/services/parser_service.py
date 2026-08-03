"""
Parser Service — Mengirim teks OCR ke Groq API dan mengekstrak JSON terstruktur.
"""

import json
import re
from pathlib import Path

from groq import Groq

from app.core.config import settings
from app.core.logger import logger
from app.services.ocr_service import OCRResult

# Load prompt dari file Markdown saat module di-import
_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "receipt_parser.md"
_PROMPT_TEMPLATE: str = _PROMPT_PATH.read_text(encoding="utf-8")

# Groq client — dibuat sekali
_groq_client = Groq(api_key=settings.groq_api_key)


def _extract_json_from_response(text: str) -> dict:
    """Ekstrak JSON dari respons Groq (handle jika masih dibungkus markdown code block)."""
    # Hapus blok ```json ... ``` jika ada
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    text = re.sub(r"```\s*$", "", text).strip()
    return json.loads(text)


def parse_receipt_with_groq(ocr_result: OCRResult) -> tuple[dict, float]:
    """
    Kirim teks OCR ke Groq, parsing JSON, return (parsed_dict, llm_confidence).
    llm_confidence adalah estimasi probabilitas berdasarkan kelengkapan field yang berhasil diekstrak.
    """
    if not ocr_result.raw_text.strip():
        raise ValueError("Teks OCR kosong, tidak ada yang bisa diparse.")

    prompt = _PROMPT_TEMPLATE.replace("{{OCR_TEXT}}", ocr_result.raw_text)

    logger.info(f"[ParserService] Mengirim {len(ocr_result.lines)} baris OCR ke Groq ({settings.groq_model})...")

    response = _groq_client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,    # Deterministic untuk task ekstraksi data
        max_tokens=2048,
    )

    raw_output = response.choices[0].message.content or ""
    logger.debug(f"[ParserService] Raw Groq output:\n{raw_output[:300]}...")

    parsed = _extract_json_from_response(raw_output)

    # Estimasi LLM confidence berdasarkan kelengkapan field penting
    important_fields = ["merchant", "items", "total"]
    filled = sum(1 for f in important_fields if parsed.get(f))
    llm_confidence = filled / len(important_fields)

    logger.info(f"[ParserService] Parsing selesai. LLM confidence estimasi: {llm_confidence:.2f}")
    return parsed, llm_confidence
