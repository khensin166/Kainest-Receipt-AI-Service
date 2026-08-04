from pydantic import BaseModel, Field
from typing import Literal


class ItemAssignment(BaseModel):
    """Satu item struk yang di-assign ke satu atau lebih anggota."""
    item_name: str = Field(..., description="Nama item dari struk")
    total_price: int = Field(..., ge=0, description="Total harga item (qty x price)")
    assigned_to: list[str] = Field(..., min_length=1, description="Daftar anggota yang menanggung item ini (dibagi rata di antara mereka)")


class SplitBillRequest(BaseModel):
    """Request body untuk endpoint POST /receipt/split."""
    mode: Literal["itemized", "equal"] = Field(
        ...,
        description="Mode split: 'itemized' (assign item per orang) atau 'equal' (bagi rata total)"
    )
    merchant: str | None = Field(None, description="Nama merchant untuk summary text")
    subtotal: int = Field(..., ge=0)
    tax: int = Field(0, ge=0)
    service: int = Field(0, ge=0)
    other_fees: int = Field(0, ge=0, description="Biaya ongkir, platform fee, dll yang dialokasikan proporsional")
    discount: int = Field(0, ge=0)
    total: int = Field(..., ge=0)
    members: list[str] = Field(..., min_length=2, description="Daftar nama anggota (min. 2 orang)")
    assignments: list[ItemAssignment] | None = Field(
        None,
        description="Diperlukan jika mode='itemized'. Daftar assignment item ke anggota."
    )

