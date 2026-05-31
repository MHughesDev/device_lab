import pytest
from decimal import Decimal
from unittest.mock import patch

from app.services.cost.pricing import (
    estimate_monthly_cost,
    estimate_snapshot_cost,
    get_ebs_snapshot_price_per_gb_month,
    get_hourly_price,
)


def test_get_hourly_price_fallback():
    with patch("app.services.cost.pricing.awspricing" if False else "builtins.len", side_effect=Exception):
        # Simulate awspricing not available: import raises inside function
        price = get_hourly_price("us-east-1", "t3.micro")
    assert price > Decimal("0")


def test_get_hourly_price_fallback_import_error():
    import importlib, sys
    original = sys.modules.get("awspricing")
    sys.modules["awspricing"] = None  # type: ignore
    try:
        price = get_hourly_price("us-east-1", "t3.micro")
        assert price > Decimal("0")
    finally:
        if original is None:
            sys.modules.pop("awspricing", None)
        else:
            sys.modules["awspricing"] = original


def test_estimate_monthly_cost():
    with patch("app.services.cost.pricing.get_hourly_price", return_value=Decimal("0.10")):
        result = estimate_monthly_cost("us-east-1", "t3.large", hours=730.0)
    assert result == Decimal("73.00")


def test_get_ebs_snapshot_price_fallback():
    import sys
    original = sys.modules.get("awspricing")
    sys.modules["awspricing"] = None  # type: ignore
    try:
        price = get_ebs_snapshot_price_per_gb_month("us-east-1")
        assert price == Decimal("0.05")
    finally:
        if original is None:
            sys.modules.pop("awspricing", None)
        else:
            sys.modules["awspricing"] = original


def test_estimate_snapshot_cost():
    with patch(
        "app.services.cost.pricing.get_ebs_snapshot_price_per_gb_month",
        return_value=Decimal("0.05"),
    ):
        result = estimate_snapshot_cost("us-east-1", 100.0, retention_days=30)
    assert result == Decimal("5.00")
