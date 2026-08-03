from fastapi import APIRouter, UploadFile, File
from app.models.response import ReceiptScanResponse
from app.services.receipt_service import process_receipt_pipeline

router = APIRouter(prefix="/receipt", tags=["Receipt"])


@router.post(
    "/scan",
    response_model=ReceiptScanResponse,
    summary="Scan Struk Belanja",
    description=(
        "Upload foto struk belanja (JPG, PNG, WEBP, HEIC). "
        "Service akan menjalankan OCR menggunakan Surya, lalu mem-parsing hasilnya "
        "dengan Groq LLM menjadi JSON terstruktur beserta confidence score."
    ),
)
async def scan_receipt(
    image: UploadFile = File(..., description="File gambar struk belanja (JPG/PNG/WEBP/HEIC, maks 10MB)")
):
    return await process_receipt_pipeline(image)
