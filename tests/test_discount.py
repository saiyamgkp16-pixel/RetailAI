"""
test_discount.py - Unit Tests for Discount Simulator & Recommendation Engine
Part of RetailPulse AI Test Suite
"""

import pytest
import pandas as pd
from discount_engine import simulate_discount, recommend_discount


def test_simulate_discount_standard():
    """TC-D01: Standard discount scenario calculation."""
    # Price: 1500, Cost: 1000, 10% discount
    # Discounted price: 1350, Profit: 350, Margin: (350 / 1350) * 100 = 25.93%
    result = simulate_discount(
        selling_price=1500.0,
        unit_cost=1000.0,
        target_margin=0.20,
        discount_percent=10.0
    )
    assert result["discounted_price"] == 1350.0
    assert result["discount_amount"] == 150.0
    assert result["new_unit_profit"] == 350.0
    assert result["new_margin_percent"] == 25.93
    assert result["target_margin_maintained"] is True
    assert result["uplift_feasible"] is True


def test_simulate_discount_max_allowable():
    """TC-D02: Target margin preservation & max allowable discount."""
    # Price: 1500, Cost: 1000, Target margin: 20% (0.20)
    # Min target price = 1000 / 0.80 = 1250
    # Max discount = (1 - 1250 / 1500) * 100 = (1 - 0.8333) * 100 = 16.67%
    result = simulate_discount(
        selling_price=1500.0,
        unit_cost=1000.0,
        target_margin=0.20,
        discount_percent=0.0
    )
    assert result["minimum_target_price"] == 1250.0
    assert result["max_allowable_discount_percent"] == 16.67


def test_simulate_discount_loss_scenario():
    """TC-D03: Discount that pushes price below unit cost."""
    # Price: 1200, Cost: 1000, 25% discount -> Price: 900 (< Cost)
    result = simulate_discount(
        selling_price=1200.0,
        unit_cost=1000.0,
        target_margin=0.20,
        discount_percent=25.0
    )
    assert result["discounted_price"] == 900.0
    assert result["new_unit_profit"] == -100.0
    assert result["target_margin_maintained"] is False
    assert result["uplift_feasible"] is False
    assert "CRITICAL WARNING" in result["uplift_explanation"]


def test_volume_uplift_calculation():
    """TC-D04: Required volume uplift mathematical correctness."""
    # Current profit: 500 (Price 1500, Cost 1000)
    # At 20% discount: Price 1200, Profit 200
    # Uplift = (500 / 200 - 1) * 100 = (2.5 - 1) * 100 = 150.0%
    result = simulate_discount(
        selling_price=1500.0,
        unit_cost=1000.0,
        target_margin=0.10,
        discount_percent=20.0
    )
    assert result["required_volume_uplift_percent"] == 150.0


def test_recommendation_battery_complaints():
    """TC-D05: Heuristic Rule - Wireless Headphones with recurring battery complaints."""
    product = {
        "product_id": "PRD002",
        "product_name": "Aura Sound Wireless Headphones",
        "purchase_cost": 950.0,
        "variable_cost": 50.0,
        "selling_price": 1499.0,
        "stock": 100,
        "inventory_age_days": 45,
        "target_margin": 0.30
    }
    reviews = pd.DataFrame([
        {"product_id": "PRD002", "rating": 2, "review_text": "Battery drains in 1 hour"},
        {"product_id": "PRD002", "rating": 1, "review_text": "Terrible battery life, charging case dead"},
        {"product_id": "PRD002", "rating": 3, "review_text": "Battery issues on calls"}
    ])
    rec = recommend_discount(product, reviews_df=reviews)
    assert rec["action_type"] == "Investigate product quality or customer complaints first."
    assert "battery" in rec["recurring_complaints"]


def test_recommendation_fast_mover_low_stock():
    """TC-D06: Heuristic Rule - High velocity and low inventory."""
    product = {
        "product_id": "PRD001",
        "product_name": "Green Tea",
        "purchase_cost": 220.0,
        "variable_cost": 30.0,
        "selling_price": 450.0,
        "stock": 12,
        "inventory_age_days": 10,
        "target_margin": 0.35
    }
    # Sales dataframe with high recent volume
    dates = pd.date_range(end="2026-11-20", periods=20, freq="D")
    sales = pd.DataFrame({
        "product_id": ["PRD001"] * 20,
        "date": dates,
        "units_sold": [10] * 20,
        "unit_selling_price": [450.0] * 20
    })
    reviews = pd.DataFrame([{"product_id": "PRD001", "rating": 5, "review_text": "Aroma is great"}])
    rec = recommend_discount(product, sales_df=sales, reviews_df=reviews)
    assert rec["action_type"] == "Avoid an unnecessary discount."


def test_recommendation_old_inventory():
    """TC-D07: Heuristic Rule - Aged inventory (> 60 days)."""
    product = {
        "product_id": "PRD005",
        "product_name": "Vintage Bag",
        "purchase_cost": 850.0,
        "variable_cost": 50.0,
        "selling_price": 1899.0,
        "stock": 50,
        "inventory_age_days": 95,
        "target_margin": 0.40
    }
    reviews = pd.DataFrame([{"product_id": "PRD005", "rating": 4, "review_text": "Nice bag"}])
    rec = recommend_discount(product, reviews_df=reviews)
    assert rec["action_type"] == "Consider a phased markdown for slow-moving or old inventory."
