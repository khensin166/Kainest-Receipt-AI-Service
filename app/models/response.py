from pydantic import BaseModel, Field
from typing import Any


# ===========================================================================
# Sub-schemas
# ===========================================================================

class ReceiptItem(BaseModel):
    id: str
    name: str
    qty: float
    price: int
    total_price: int


class ValidationResult(BaseModel):
    is_valid: bool
    warnings: list[str] = []


class CycleInfo(BaseModel):
    label: str
    date_range: str | None = None


# ===========================================================================
# Scan Response Schema
# ===========================================================================

class ReceiptData(BaseModel):
    document_type: str | None = "receipt"
    merchant: str | None = None
    date: str | None = None
    time: str | None = None
    currency: str = "IDR"
    items: list[ReceiptItem] = []
    subtotal: int = Field(0, description="Total sebelum pajak, service, diskon, dll")
    tax: int = Field(0, description="Nominal pajak/PPN")
    service: int = Field(0, description="Nominal biaya layanan")
    other_fees: int = Field(0, description="Biaya lain-lain, platform fee, ongkir")
    discount: int = Field(0, description="Nominal diskon")
    total: int = 0
    payment_method: str | None = None
    validation: ValidationResult
    raw_ocr_preview: str | None = None


class ReceiptScanResponse(BaseModel):
    code: int = 200
    status: str = "success"
    confidence: float = Field(..., ge=0.0, le=1.0, description="Skor kepercayaan gabungan OCR + LLM parsing (0.0 – 1.0)")
    data: ReceiptData


# ===========================================================================
# Split Bill Response Schema
# ===========================================================================

class MemberBreakdown(BaseModel):
    member_name: str
    items: list[str]
    item_subtotal: int
    proportional_tax: int
    proportional_service: int
    proportional_discount: int
    total_to_pay: int


class SplitBillData(BaseModel):
    mode: str
    total_amount: int
    breakdown: list[MemberBreakdown]
    summary_text: str = Field(..., description="Teks siap salin ke WhatsApp")


class SplitBillResponse(BaseModel):
    code: int = 200
    status: str = "success"
    data: SplitBillData


# ===========================================================================
# Health & Generic Error Response
# ===========================================================================

class HealthData(BaseModel):
    status: str = "ok"
    service: str = "kainest-receipt-ai-service"


class HealthResponse(BaseModel):
    code: int = 200
    status: str = "success"
    data: HealthData


class ErrorResponse(BaseModel):
    code: int
    status: str = "error"
    message: str
    detail: Any = None
