"""
Receipt Service — Orkestrator utama pipeline OCR + Parsing + Validasi.
"""

import uuid

from fastapi import UploadFile, HTTPException

from app.core.config import settings
from app.core.constants import ALLOWED_IMAGE_TYPES
from app.core.logger import logger
from app.models.response import ReceiptData, ReceiptItem, ReceiptScanResponse, ValidationResult
from app.services.image_service import preprocess_image, cleanup_temp, convert_pdf_to_images
from app.services.ocr_service import run_ocr, OCRResult
from app.services.parser_service import parse_receipt_with_groq
from app.services.validation_service import validate_receipt


async def process_receipt_pipeline(file: UploadFile) -> ReceiptScanResponse:
    """
    Pipeline lengkap:
    1. Validasi file
    2. Preprocessing gambar
    3. Surya OCR
    4. Groq LLM Parsing
    5. Validasi aritmatika
    6. Return structured response
    """
    # 1. Validasi format file
    content_type = file.content_type or ""
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Tipe file tidak didukung: {content_type}. Gunakan JPG, PNG, WEBP, atau HEIC."
        )

    file_bytes = await file.read()

    # Cek ukuran file
    max_bytes = settings.max_image_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File terlalu besar. Maksimum {settings.max_image_size_mb}MB."
        )

    temp_paths = []
    try:
        # 2. Preprocessing & Ekstraksi Gambar
        logger.info(f"[ReceiptService] Memulai pipeline untuk file: {file.filename} ({content_type})")
        if content_type == "application/pdf":
            image_items = convert_pdf_to_images(file_bytes)
        else:
            pil_image, temp_path = preprocess_image(file_bytes)
            image_items = [(pil_image, temp_path)]

        for _, tpath in image_items:
            temp_paths.append(tpath)

        # 3. OCR pada setiap gambar (halaman)
        all_lines = []
        confidences = []
        for img, _ in image_items:
            ocr_res = run_ocr(img)
            all_lines.extend(ocr_res.lines)
            confidences.append(ocr_res.avg_confidence)
            
        if not all_lines:
            raise ValueError("Tidak ada teks yang terdeteksi dari dokumen ini.")

        # Gabungkan hasil (stitch)
        combined_raw_text = "\n".join(ln.text for ln in all_lines)
        ocr_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        ocr_result = OCRResult(
            lines=all_lines,
            avg_confidence=ocr_confidence,
            raw_text=combined_raw_text
        )

        # 4. LLM Parsing
        parsed, llm_confidence = parse_receipt_with_groq(ocr_result)

        # 5. Validasi aritmatika
        validation_result = validate_receipt(parsed)

        # 6. Susun items dengan ID unik
        raw_items = parsed.get("items") or []
        items = []
        for i, item in enumerate(raw_items, 1):
            items.append(ReceiptItem(
                id=f"item_{i}",
                name=item.get("name") or "Unknown Item",
                qty=item.get("qty") or 1,
                price=item.get("price") or 0,
                total_price=item.get("total_price") or 0,
            ))

        # 7. Gabungkan confidence score (rata-rata OCR dan LLM)
        combined_confidence = round((ocr_confidence + llm_confidence) / 2, 3)

        receipt_data = ReceiptData(
            document_type=parsed.get("document_type") or "receipt",
            merchant=parsed.get("merchant"),
            date=parsed.get("date"),
            time=parsed.get("time"),
            currency=parsed.get("currency") or "IDR",
            items=items,
            subtotal=parsed.get("subtotal") or 0,
            tax=parsed.get("tax") or 0,
            service=parsed.get("service") or 0,
            other_fees=parsed.get("other_fees") or 0,
            discount=parsed.get("discount") or 0,
            total=parsed.get("total") or 0,
            payment_method=parsed.get("payment_method"),
            validation=ValidationResult(**validation_result),
            raw_ocr_preview=ocr_result.raw_text[:500] if ocr_result.raw_text else None,
        )

        logger.info(f"[ReceiptService] Pipeline selesai. Confidence: {combined_confidence}")
        return ReceiptScanResponse(
            code=200,
            status="success",
            confidence=combined_confidence,
            data=receipt_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[ReceiptService] Pipeline error: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal memproses struk: {str(e)}")
    finally:
        for tpath in temp_paths:
            cleanup_temp(tpath)
