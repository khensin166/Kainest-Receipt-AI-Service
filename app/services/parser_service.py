"""
Parser Service — Mengirim teks OCR ke Groq API dan mengekstrak JSON terstruktur.
Menggunakan mekanisme fallback model otomatis (identik dengan Kainest Backend).
Model gpt-oss-120b adalah reasoning model: wajib stream=True + max_completion_tokens.
"""

import json
import re
from pathlib import Path
from typing import Optional

from groq import Groq

from app.core.config import settings
from app.core.logger import logger
from app.services.ocr_service import OCRResult

# Load prompt dari file Markdown saat module di-import
_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "receipt_parser.md"
_PROMPT_TEMPLATE: str = _PROMPT_PATH.read_text(encoding="utf-8")

# Groq client — dibuat sekali, membaca GROQ_API_KEY dari env secara otomatis
_groq_client = Groq(api_key=settings.groq_api_key)

# Daftar model yang akan dicoba secara berurutan (fallback otomatis).
# Dibaca dari env GROQ_MODELS (comma-separated), fallback ke default jika kosong.
FALLBACK_MODELS: list[str] = [
    m.strip()
    for m in settings.groq_models.split(",")
    if m.strip()
]


def _extract_json_from_response(text: str) -> dict:
    """Ekstrak JSON dari respons LLM (handle jika masih dibungkus markdown code block)."""
    # Hapus blok ```json ... ``` jika ada
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    text = re.sub(r"```\s*$", "", text).strip()
    return json.loads(text)


def _call_llm_with_fallback(prompt: str) -> tuple[str, str]:
    """
    Kirim prompt ke LLM dengan mekanisme fallback model otomatis.
    Identik dengan pola groqService.ts di Kainest Backend.
    Menggunakan stream=True agar tidak timeout saat model reasoning berpikir.

    Returns:
        (raw_output, model_used)
    Raises:
        RuntimeError: jika semua model gagal.
    """
    last_error: Optional[Exception] = None

    for model_name in FALLBACK_MODELS:
        try:
            logger.debug(f"[ParserService] Mencoba model: {model_name}")

            completion = _groq_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=1,
                max_completion_tokens=2048,
                top_p=1,
                reasoning_effort="medium",
                stream=True,
                stop=None,
            )

            # Gabungkan semua chunk streaming menjadi satu string utuh
            raw_output = ""
            for chunk in completion:
                delta_content = chunk.choices[0].delta.content or ""
                raw_output += delta_content

            logger.info(f"[ParserService] ✅ Berhasil menggunakan model: {model_name}")
            return raw_output, model_name

        except Exception as exc:
            logger.warning(
                f"[ParserService] ⚠️ Model {model_name} gagal, mencoba selanjutnya... "
                f"({type(exc).__name__}: {exc})"
            )
            last_error = exc

    # Semua model gagal
    logger.error("[ParserService] ❌ Semua model AI gagal digunakan.")
    raise RuntimeError(
        f"Semua model AI gagal digunakan. Error terakhir: {last_error}"
    )


def parse_receipt_with_groq(ocr_result: OCRResult) -> tuple[dict, float]:
    """
    Kirim teks OCR ke Groq (dengan fallback), parsing JSON,
    return (parsed_dict, llm_confidence).
    llm_confidence adalah estimasi probabilitas berdasarkan kelengkapan field yang berhasil diekstrak.
    """
    if not ocr_result.raw_text.strip():
        raise ValueError("Teks OCR kosong, tidak ada yang bisa diparse.")

    prompt = _PROMPT_TEMPLATE.replace("{{OCR_TEXT}}", ocr_result.raw_text)

    logger.info(
        f"[ParserService] Mengirim {len(ocr_result.lines)} baris OCR ke Groq "
        f"(priority: {FALLBACK_MODELS[0] if FALLBACK_MODELS else 'N/A'})..."
    )

    raw_output, used_model = _call_llm_with_fallback(prompt)
    logger.debug(f"[ParserService] Raw output dari {used_model}:\n{raw_output[:300]}...")

    parsed = _extract_json_from_response(raw_output)

    # Estimasi LLM confidence berdasarkan kelengkapan field penting
    important_fields = ["merchant", "items", "total"]
    filled = sum(1 for f in important_fields if parsed.get(f))
    llm_confidence = filled / len(important_fields)

    logger.info(f"[ParserService] Parsing selesai. LLM confidence estimasi: {llm_confidence:.2f}")
    return parsed, llm_confidence
