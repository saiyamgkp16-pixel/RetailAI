"""
test_analytics.py - Unit Tests for Analytics and Metric Aggregation
Part of RetailPulse AI Test Suite
"""

import pytest
import pandas as pd
from analytics import load_all_data, get_dashboard_metrics, get_sales_trend, get_product_performance


def test_load_all_data():
    """Verify loading and data cleansing of all 4 CSV datasets."""
    data = load_all_data("data")
    assert "products" in data
    assert "sales" in data
    assert "reviews" in data
    assert "competitors" in data

    products = data["products"]
    sales = data["sales"]
    reviews = data["reviews"]
    competitors = data["competitors"]

    assert not products.empty
    assert len(products) >= 5
    assert "unit_cost" in products.columns
    assert "unit_profit" in products.columns
    assert "margin_pct" in products.columns

    assert not sales.empty
    assert "revenue" in sales.columns

    # Foreign key integrity check
    valid_pids = set(products["product_id"])
    assert set(sales["product_id"]).issubset(valid_pids)
    assert set(reviews["product_id"]).issubset(valid_pids)
    assert set(competitors["product_id"]).issubset(valid_pids)


def test_dashboard_metrics():
    """Verify overall portfolio KPI aggregation."""
    data = load_all_data("data")
    metrics = get_dashboard_metrics(data["products"], data["sales"], data["reviews"])

    assert metrics["active_skus"] >= 5
    assert metrics["total_revenue"] > 0
    assert metrics["total_gross_profit"] > 0
    assert metrics["total_units_sold"] > 0
    assert 1.0 <= metrics["avg_rating"] <= 5.0
    assert metrics["total_inventory"] > 0
    assert metrics["overall_margin_pct"] > 0


def test_sales_trend():
    """Verify daily sales trend aggregation."""
    data = load_all_data("data")
    trend = get_sales_trend(data["sales"])
    assert not trend.empty
    assert "date" in trend.columns
    assert "units_sold" in trend.columns
    assert "revenue" in trend.columns


def test_product_performance():
    """Verify product-level unified performance calculation."""
    data = load_all_data("data")
    perf = get_product_performance(data["products"], data["sales"], data["reviews"])
    assert not perf.empty
    assert "total_gross_profit" in perf.columns
    assert "avg_rating" in perf.columns
    assert "performance_tag" in perf.columns
