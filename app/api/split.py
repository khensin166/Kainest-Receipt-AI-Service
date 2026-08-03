from fastapi import APIRouter, HTTPException, Depends
from app.models.request import SplitBillRequest
from app.models.response import SplitBillResponse
from app.services.split_service import calculate_split
from app.core.security import verify_api_token

router = APIRouter(
    prefix="/receipt",
    tags=["Split Bill"],
    dependencies=[Depends(verify_api_token)]
)


@router.post(
    "/split",
    response_model=SplitBillResponse,
    summary="Kalkulasi Split Bill",
    description=(
        "Hitung pembagian tagihan struk ke beberapa anggota. "
        "Tersedia dua mode:\n"
        "- **itemized**: Assign item tertentu ke orang tertentu, pajak dialokasikan proporsional.\n"
        "- **equal**: Bagi total secara merata ke semua anggota.\n\n"
        "Response menyertakan breakdown per anggota dan teks ringkasan siap salin ke WhatsApp."
    ),
)
async def split_bill(req: SplitBillRequest):
    try:
        split_data = calculate_split(req)
        return SplitBillResponse(code=200, status="success", data=split_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
