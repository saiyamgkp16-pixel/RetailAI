"""
test_pricing.py - Unit Tests for Pricing Engine
Part of RetailPulse AI Test Suite
"""

import pytest
import pandas as pd
from pricing_engine import (
    calculate_unit_cost,
    calculate_unit_profit,
    calculate_margin,
    calculate_minimum_price,
    calculate_price_metrics,
)


def test_unit_cost_calculation():
    """Verify purchase cost + variable cost summation."""
    assert calculate_unit_cost(1000.0, 50.0) == 1050.0
    assert calculate_unit_cost(250.0, 0.0) == 250.0
    assert calculate_unit_cost(0.0, 0.0) == 0.0


def test_unit_profit_calculation():
    """Verify unit profit = selling price - unit cost."""
    assert calculate_unit_profit(1499.0, 1000.0) == 499.0
    assert calculate_unit_profit(1000.0, 1000.0) == 0.0
    assert calculate_unit_profit(800.0, 1000.0) == -200.0


def test_margin_and_markup_normal():
    """TC-P01: Normal positive profit margin and markup."""
    # Selling price: 1500, Unit cost: 1000 -> Profit: 500
    # Margin: 500 / 1500 = 33.33%
    # Markup: 500 / 1000 = 50.0%
    result = calculate_margin(1500.0, 1000.0)
    assert result["unit_profit"] == 500.0
    assert result["margin_percent"] == 33.33
    assert result["markup_percent"] == 50.0


def test_margin_zero_profit():
    """TC-P02: Selling at exact cost (zero profit)."""
    result = calculate_margin(1000.0, 1000.0)
    assert result["unit_profit"] == 0.0
    assert result["margin_percent"] == 0.0
    assert result["markup_percent"] == 0.0


def test_margin_below_cost_loss():
    """TC-P03: Selling price below unit cost (negative profit)."""
    result = calculate_margin(800.0, 1000.0)
    assert result["unit_profit"] == -200.0
    assert result["margin_percent"] == -25.0
    assert result["markup_percent"] == -20.0


def test_minimum_price_target_margin():
    """TC-P04: Target margin minimum price formula."""
    # Unit cost = 1000, Target margin = 20% (0.20)
    # Min price = 1000 / (1 - 0.20) = 1250.0
    # Check: (1250 - 1000) / 1250 = 250 / 1250 = 20%
    min_price = calculate_minimum_price(1000.0, 0.20)
    assert min_price == 1250.0

    # Also accepts percentage format e.g. 20.0
    min_price_pct = calculate_minimum_price(1000.0, 20.0)
    assert min_price_pct == 1250.0


def test_minimum_price_zero_margin():
    """TC-P05: 0% target margin means min price equals unit cost."""
    min_price = calculate_minimum_price(850.0, 0.0)
    assert min_price == 850.0


def test_minimum_price_invalid_margin():
    """TC-P06: Target margin >= 100% or negative should raise ValueError."""
    with pytest.raises(ValueError):
        calculate_minimum_price(1000.0, 1.0)
    with pytest.raises(ValueError):
        calculate_minimum_price(1000.0, 105.0)
    with pytest.raises(ValueError):
        calculate_minimum_price(1000.0, -0.10)


def test_price_metrics_with_competitors():
    """TC-P07: Test full price metrics generation with competitor median."""
    product = {
        "product_id": "PRD002",
        "product_name": "Wireless Headphones",
        "purchase_cost": 950.0,
        "variable_cost": 50.0,
        "selling_price": 1499.0,
        "target_margin": 0.30
    }
    competitors = pd.DataFrame([
        {"product_id": "PRD002", "competitor_name": "A", "competitor_price": 1450.0},
        {"product_id": "PRD002", "competitor_name": "B", "competitor_price": 1500.0},
        {"product_id": "PRD002", "competitor_name": "C", "competitor_price": 1550.0},
    ])
    metrics = calculate_price_metrics(product, competitors)
    assert metrics["unit_cost"] == 1000.0
    assert metrics["unit_profit"] == 499.0
    assert metrics["competitor_median"] == 1500.0
    assert metrics["target_margin_achieved"] is True


def test_price_metrics_empty_competitor():
    """Verify metrics calculation when competitor data is empty or missing."""
    product = {
        "product_id": "PRD999",
        "product_name": "New Item",
        "purchase_cost": 400.0,
        "variable_cost": 0.0,
        "selling_price": 600.0,
        "target_margin": 0.25
    }
    metrics = calculate_price_metrics(product, None)
    assert metrics["competitor_median"] is None
    assert metrics["competitor_count"] == 0
