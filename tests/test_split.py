"""Tests: Split Bill Engine kalkulasi."""
import pytest
from app.models.request import SplitBillRequest, ItemAssignment
from app.services.split_service import calculate_split


BASE_REQ = {
    "subtotal": 60000,
    "tax": 6000,
    "service": 3000,
    "discount": 0,
    "total": 69000,
    "members": ["Budi", "Ani", "Caca"],
    "merchant": "Test Resto",
}


def test_equal_split_divides_evenly():
    req = SplitBillRequest(mode="equal", **BASE_REQ)
    result = calculate_split(req)
    total_paid = sum(m.total_to_pay for m in result.breakdown)
    assert total_paid == 69000
    # Setiap orang bayar kira-kira 23000 (69000 / 3)
    for member in result.breakdown:
        assert 22999 <= member.total_to_pay <= 23001


def test_itemized_split_correct_total():
    assignments = [
        ItemAssignment(item_name="Nasi Goreng", total_price=50000, assigned_to=["Budi", "Ani"]),
        ItemAssignment(item_name="Es Teh", total_price=10000, assigned_to=["Caca"]),
    ]
    req = SplitBillRequest(mode="itemized", assignments=assignments, **BASE_REQ)
    result = calculate_split(req)
    total_paid = sum(m.total_to_pay for m in result.breakdown)
    assert total_paid == 69000


def test_itemized_requires_assignments():
    req = SplitBillRequest(mode="itemized", **BASE_REQ)  # Tanpa assignments
    with pytest.raises(ValueError, match="assignments"):
        calculate_split(req)


def test_summary_text_contains_member_names():
    req = SplitBillRequest(mode="equal", **BASE_REQ)
    result = calculate_split(req)
    for member in BASE_REQ["members"]:
        assert member in result.summary_text
