"""
Split Bill Service — Engine kalkulasi pembagian tagihan.

Mendukung dua mode:
  - "itemized" : Setiap item di-assign ke satu atau lebih anggota secara spesifik.
  - "equal"    : Total dibagi rata ke semua anggota.

Pajak, Service, dan Diskon dialokasikan secara proporsional berdasarkan
porsi belanjaan dasar (item subtotal) masing-masing anggota.
"""

from app.core.logger import logger
from app.models.request import SplitBillRequest
from app.models.response import MemberBreakdown, SplitBillData


def _format_rupiah(amount: int) -> str:
    return f"Rp {amount:,}".replace(",", ".")


def _build_summary_text(merchant: str | None, breakdown: list[MemberBreakdown], total: int) -> str:
    """Buat teks ringkasan siap salin ke WhatsApp."""
    merchant_label = merchant or "Struk Belanja"
    lines = [f"📋 *Rincian Split Bill — {merchant_label}*", f"Total: {_format_rupiah(total)}", ""]
    for i, m in enumerate(breakdown, 1):
        lines.append(f"{i}. 👤 *{m.member_name}*: {_format_rupiah(m.total_to_pay)}")
        for item_label in m.items:
            lines.append(f"   • {item_label}")
    lines.append("")
    lines.append("_Dibuat otomatis oleh Kainest Receipt AI_")
    return "\n".join(lines)


def calculate_split_itemized(req: SplitBillRequest) -> SplitBillData:
    """Mode Itemized: assign item ke anggota, alokasikan pajak proporsional."""
    assignments = req.assignments or []
    members = req.members

    # Akumulasi subtotal per anggota dari assignment
    member_subtotals: dict[str, int] = {m: 0 for m in members}
    member_items: dict[str, list[str]] = {m: [] for m in members}

    for assignment in assignments:
        per_person_price = round(assignment.total_price / len(assignment.assigned_to))
        for member in assignment.assigned_to:
            if member not in member_subtotals:
                logger.warning(f"[SplitService] Anggota '{member}' dalam assignment tidak ada di daftar members.")
                member_subtotals[member] = 0
                member_items[member] = []
            member_subtotals[member] += per_person_price
            share_label = f"(1/{len(assignment.assigned_to)})" if len(assignment.assigned_to) > 1 else ""
            member_items[member].append(f"{assignment.item_name} {share_label}".strip())

    total_item_subtotal = sum(member_subtotals.values()) or 1  # Hindari division by zero
    
    # Jika total tidak pas (karena pembulatan atau other_fees tidak dikirim), hitung selisihnya sebagai fallback
    explicit_other_fees = req.other_fees
    calc_without_other = total_item_subtotal + req.tax + req.service - req.discount
    # Gunakan other_fees eksplisit jika ada, jika tidak fallback ke selisih dari total
    if explicit_other_fees == 0 and req.total > calc_without_other:
        explicit_other_fees = req.total - calc_without_other

    breakdown: list[MemberBreakdown] = []
    for member in members:
        sub = member_subtotals.get(member, 0)
        ratio = sub / total_item_subtotal

        prop_tax = round(req.tax * ratio)
        prop_service = round(req.service * ratio)
        prop_other_fees = round(explicit_other_fees * ratio)
        prop_discount = round(req.discount * ratio)
        
        # total_to_pay mencakup subtotal, pajak, service, other_fees, dan dikurangi diskon proporsional
        total_to_pay = sub + prop_tax + prop_service + prop_other_fees - prop_discount

        breakdown.append(MemberBreakdown(
            member_name=member,
            items=member_items.get(member, []),
            item_subtotal=sub,
            proportional_tax=prop_tax,
            proportional_service=prop_service,
            proportional_discount=prop_discount,
            total_to_pay=total_to_pay,
        ))

    # Koreksi selisih pembulatan → tambahkan ke anggota pertama
    calculated_total = sum(m.total_to_pay for m in breakdown)
    diff = req.total - calculated_total
    if diff != 0 and breakdown:
        breakdown[0].total_to_pay += diff

    summary_text = _build_summary_text(req.merchant, breakdown, req.total)
    return SplitBillData(mode="itemized", total_amount=req.total, breakdown=breakdown, summary_text=summary_text)


def calculate_split_equal(req: SplitBillRequest) -> SplitBillData:
    """Mode Bagi Rata: total dibagi merata ke semua anggota."""
    n = len(req.members)
    base_amount = req.total // n
    remainder = req.total - (base_amount * n)

    breakdown: list[MemberBreakdown] = []
    for i, member in enumerate(req.members):
        extra = 1 if i < remainder else 0  # Distribusi sisa Rp ke anggota pertama
        total_to_pay = base_amount + extra
        breakdown.append(MemberBreakdown(
            member_name=member,
            items=["Semua item (bagi rata)"],
            item_subtotal=round(req.subtotal / n),
            proportional_tax=round(req.tax / n),
            proportional_service=round((req.service + req.other_fees) / n),
            proportional_discount=round(req.discount / n),
            total_to_pay=total_to_pay,
        ))

    summary_text = _build_summary_text(req.merchant, breakdown, req.total)
    return SplitBillData(mode="equal", total_amount=req.total, breakdown=breakdown, summary_text=summary_text)


def calculate_split(req: SplitBillRequest) -> SplitBillData:
    """Entry point utama — pilih mode dan delegasikan ke fungsi yang sesuai."""
    logger.info(f"[SplitService] Menghitung split bill mode='{req.mode}' untuk {len(req.members)} anggota")
    if req.mode == "equal":
        return calculate_split_equal(req)
    elif req.mode == "itemized":
        if not req.assignments:
            raise ValueError("Mode 'itemized' memerlukan field 'assignments' yang tidak boleh kosong.")
        return calculate_split_itemized(req)
    else:
        raise ValueError(f"Mode split tidak dikenali: {req.mode}")
