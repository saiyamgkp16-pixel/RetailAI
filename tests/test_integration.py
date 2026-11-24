"""
test_integration.py - Full System Integration Tests
Part of RetailPulse AI Test Suite
"""

import pytest
import pandas as pd
from analytics import load_all_data, get_dashboard_metrics, get_sales_trend, get_product_performance
from pricing_engine import calculate_price_metrics, calculate_margin, calculate_minimum_price
from discount_engine import simulate_discount, recommend_discount
from review_engine import analyze_reviews
from retail_advisor import compile_product_context, ask_retail_advisor
from nvidia_client import check_nvidia_connection, get_nvidia_config


def test_full_pipeline_demo_scenario_prd002():
    """
    Mandatory Demonstration Scenario:
    Product: Aura Sound Wireless Bluetooth Headphones (PRD002)
    Purchase cost: ₹950 + Variable cost: ₹50 = ₹1,000 unit cost
    Selling price: ₹1,499
    Stock: 100 units
    Business situation: Declining sales and recurring battery complaints.
    """
    data = load_all_data("data")
    products = data["products"]
    sales = data["sales"]
    reviews = data["reviews"]
    competitors = data["competitors"]

    p_row = products[products["product_id"] == "PRD002"].iloc[0]
    assert p_row["purchase_cost"] == 950.0
    assert p_row["variable_cost"] == 50.0
    assert p_row["unit_cost"] == 1000.0
    assert p_row["selling_price"] == 1499.0
    assert p_row["stock"] == 100

    # 1. Pricing Engine Evaluation
    p_metrics = calculate_price_metrics(p_row, competitors)
    assert p_metrics["unit_cost"] == 1000.0
    assert p_metrics["unit_profit"] == 499.0
    assert p_metrics["margin_percent"] == 33.29
    assert p_metrics["target_margin_percent"] == 30.0
    # Min price for 30% margin: 1000 / 0.70 = 1428.57
    assert p_metrics["minimum_price_for_target"] == 1428.57
    assert p_metrics["target_margin_achieved"] is True
    assert p_metrics["competitor_median"] is not None

    # 2. Customer Reviews Evaluation
    rev_analysis = analyze_reviews("PRD002", reviews, use_ai=False)
    assert rev_analysis["average_rating"] < 3.5
    assert any("battery" in c.lower() for c in rev_analysis["common_complaints"])

    # 3. Discount Engine Recommendation
    rec = recommend_discount(p_row, sales, reviews, competitors)
    assert rec["action_type"] == "Investigate product quality or customer complaints first."
    assert "battery" in rec["recurring_complaints"]

    # 4. Discount Simulation at 10%
    sim = simulate_discount(1499.0, 1000.0, 0.30, 10.0)
    assert sim["discounted_price"] == 1349.10
    assert sim["new_unit_profit"] == 349.10
    # New margin: 349.10 / 1349.10 = 25.88% (< 30% target)
    assert sim["new_margin_percent"] == 25.88
    assert sim["target_margin_maintained"] is False
    assert sim["uplift_feasible"] is True

    # 5. Retail Advisor Q&A (Local Fallback)
    ctx = compile_product_context("PRD002", products, sales, reviews, competitors)
    advisor_resp = ask_retail_advisor("Why are sales declining?", ctx)
    assert advisor_resp["answer"] != ""
    assert "battery" in advisor_resp["answer"].lower()
    assert "Investigate" in advisor_resp["answer"]


def test_all_five_demo_skus_loaded_and_analyzable():
    """Verify all 5 required business scenarios are loadable and analyzable."""
    data = load_all_data("data")
    products = data["products"]
    sales = data["sales"]
    reviews = data["reviews"]
    competitors = data["competitors"]

    expected_skus = ["PRD001", "PRD002", "PRD003", "PRD004", "PRD005"]
    assert set(expected_skus).issubset(set(products["product_id"]))

    for pid in expected_skus:
        ctx = compile_product_context(pid, products, sales, reviews, competitors)
        assert ctx["product_id"] == pid
        assert ctx["unit_cost"] > 0
        assert ctx["selling_price"] > 0
        assert len(ctx["reasons"]) > 0

        # Test advisor response
        resp = ask_retail_advisor("Should I give this product a discount?", ctx)
        assert len(resp["answer"]) > 50


def test_nvidia_client_safe_ping():
    """Verify check_nvidia_connection returns structured dict without throwing."""
    conn_info = check_nvidia_connection()
    assert isinstance(conn_info, dict)
    assert "connected" in conn_info
    assert "message" in conn_info
