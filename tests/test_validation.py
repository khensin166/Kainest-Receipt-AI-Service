"""Tests: Validation Service aritmatika."""
import pytest
from app.services.validation_service import validate_receipt


def test_valid_receipt_no_warnings():
    parsed = {
        "items": [
            {"name": "Nasi Goreng", "qty": 1, "price": 25000, "total_price": 25000},
            {"name": "Es Teh", "qty": 2, "price": 5000, "total_price": 10000},
        ],
        "subtotal": 35000,
        "tax": 3500,
        "service": 0,
        "discount": 0,
        "total": 38500,
    }
    result = validate_receipt(parsed)
    assert result["is_valid"] is True
    assert result["warnings"] == []


def test_total_mismatch_triggers_warning():
    parsed = {
        "items": [{"name": "Item A", "qty": 1, "price": 10000, "total_price": 10000}],
        "subtotal": 10000,
        "tax": 1000,
        "service": 0,
        "discount": 0,
        "total": 99999,  # Salah — seharusnya 11000
    }
    result = validate_receipt(parsed)
    assert result["is_valid"] is False
    assert len(result["warnings"]) > 0
    assert parsed["total"] == 11000  # Auto-corrected


def test_item_qty_price_mismatch_autocorrect():
    parsed = {
        "items": [{"name": "Soto", "qty": 2, "price": 15000, "total_price": 20000}],  # 20000 salah
        "subtotal": 20000,
        "tax": 0,
        "service": 0,
        "discount": 0,
        "total": 20000,
    }
    validate_receipt(parsed)
    assert parsed["items"][0]["total_price"] == 30000  # 2 × 15000
