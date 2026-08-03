"""
Validation Service — Memeriksa konsistensi aritmatika hasil parsing struk.
"""

from app.core.constants import VALIDATION_TOLERANCE_IDR
from app.core.logger import logger


def validate_receipt(parsed: dict) -> dict:
    """
    Validasi konsistensi data struk:
    ✅ Harga item tidak negatif
    ✅ total_price item = qty × price
    ✅ subtotal ≈ sum(item.total_price)
    ✅ total ≈ subtotal + tax + service + other_fees - discount

    Return dict: { "is_valid": bool, "warnings": list[str] }
    """
    warnings: list[str] = []
    items = parsed.get("items", [])
    subtotal = parsed.get("subtotal", 0) or 0
    tax = parsed.get("tax", 0) or 0
    service = parsed.get("service", 0) or 0
    other_fees = parsed.get("other_fees", 0) or 0
    discount = parsed.get("discount", 0) or 0
    total = parsed.get("total", 0) or 0

    # 1. Cek harga item tidak negatif
    for item in items:
        if (item.get("price") or 0) < 0:
            warnings.append(f"Harga item '{item.get('name')}' negatif.")
        if (item.get("total_price") or 0) < 0:
            warnings.append(f"Total harga item '{item.get('name')}' negatif.")

    # 2. Cek konsistensi qty × price = total_price
    for item in items:
        qty = item.get("qty") or 1
        price = item.get("price") or 0
        total_price = item.get("total_price") or 0
        expected = round(qty * price)
        if abs(expected - total_price) > VALIDATION_TOLERANCE_IDR:
            warnings.append(
                f"Item '{item.get('name')}': qty×price ({expected}) ≠ total_price ({total_price}). "
                f"Melakukan auto-koreksi."
            )
            item["total_price"] = expected  # Auto-fix

    # 3. Cek subtotal ≈ sum item total_price
    calc_subtotal = sum(item.get("total_price") or 0 for item in items)
    if items and abs(calc_subtotal - subtotal) > VALIDATION_TOLERANCE_IDR:
        warnings.append(
            f"Subtotal ({subtotal:,}) tidak cocok dengan jumlah item ({calc_subtotal:,}). "
            f"Melakukan auto-koreksi subtotal."
        )
        parsed["subtotal"] = calc_subtotal
        subtotal = calc_subtotal

    # 4. Cek total ≈ subtotal + tax + service + other_fees - discount
    calc_total = subtotal + tax + service + other_fees - discount
    if abs(calc_total - total) > VALIDATION_TOLERANCE_IDR:
        if calc_total < total and (total - calc_total) < (subtotal * 0.5):
            # Kemungkinan besar LLM gagal mengekstrak biaya tambahan (tax/service/other_fees)
            diff = total - calc_total
            warnings.append(
                f"Total ({total:,}) > kalkulasi item ({calc_total:,}). "
                f"Asumsi ada biaya terlewat oleh AI. Auto-koreksi other_fees (+{diff:,})."
            )
            parsed["other_fees"] = other_fees + diff
        elif calc_total > total and (calc_total - total) < (subtotal * 0.5):
            # Kemungkinan besar LLM gagal mengekstrak diskon tambahan (seperti A-Poin, promo)
            diff = calc_total - total
            warnings.append(
                f"Total ({total:,}) < kalkulasi item ({calc_total:,}). "
                f"Asumsi ada diskon terlewat oleh AI. Auto-koreksi discount (+{diff:,})."
            )
            parsed["discount"] = discount + diff
        else:
            # Jika selisihnya sangat ekstrem, kemungkinan 'total' salah baca
            warnings.append(
                f"Total ({total:,}) tidak masuk akal dibandingkan kalkulasi ({calc_total:,}). "
                f"Melakukan auto-koreksi total."
            )
            parsed["total"] = calc_total

    is_valid = len(warnings) == 0
    if warnings:
        logger.warning(f"[ValidationService] {len(warnings)} peringatan validasi: {warnings}")
    else:
        logger.info("[ValidationService] Validasi OK — semua nilai konsisten.")

    return {"is_valid": is_valid, "warnings": warnings}
