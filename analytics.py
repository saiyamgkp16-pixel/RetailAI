"""
analytics.py - Data Processing and Aggregated Business Metrics
Part of RetailPulse AI

Loads CSV datasets and executes all deterministic aggregations for the
Streamlit dashboard and charts using Pandas and NumPy.
"""

from typing import Dict, Any, Optional, Tuple
import os
import pandas as pd
import numpy as np
from pricing_engine import calculate_unit_cost


def load_all_data(data_dir: str = "data") -> Dict[str, pd.DataFrame]:
    """
    Load all CSV files from the specified directory with data type validation.
    Returns a dictionary of cleaned DataFrames.
    """
    p_path = os.path.join(data_dir, "products.csv")
    s_path = os.path.join(data_dir, "sales.csv")
    r_path = os.path.join(data_dir, "reviews.csv")
    c_path = os.path.join(data_dir, "competitors.csv")
    
    # Safe loading with fallback to empty DataFrame if file not found
    products = pd.read_csv(p_path) if os.path.exists(p_path) else pd.DataFrame()
    sales = pd.read_csv(s_path) if os.path.exists(s_path) else pd.DataFrame()
    reviews = pd.read_csv(r_path) if os.path.exists(r_path) else pd.DataFrame()
    competitors = pd.read_csv(c_path) if os.path.exists(c_path) else pd.DataFrame()
    
    # Type cleansing and parsing
    if not products.empty:
        products["product_id"] = products["product_id"].astype(str)
        products["purchase_cost"] = pd.to_numeric(products["purchase_cost"], errors="coerce").fillna(0.0)
        products["variable_cost"] = pd.to_numeric(products["variable_cost"], errors="coerce").fillna(0.0)
        products["selling_price"] = pd.to_numeric(products["selling_price"], errors="coerce").fillna(0.0)
        products["stock"] = pd.to_numeric(products["stock"], errors="coerce").fillna(0).astype(int)
        products["target_margin"] = pd.to_numeric(products["target_margin"], errors="coerce").fillna(0.30)
        products["inventory_age_days"] = pd.to_numeric(products["inventory_age_days"], errors="coerce").fillna(0).astype(int)
        products["unit_cost"] = products.apply(
            lambda r: calculate_unit_cost(r["purchase_cost"], r["variable_cost"]), axis=1
        )
        products["unit_profit"] = products["selling_price"] - products["unit_cost"]
        products["margin_pct"] = np.where(
            products["selling_price"] > 0,
            (products["unit_profit"] / products["selling_price"]) * 100.0,
            0.0
        )
        
    if not sales.empty:
        sales["product_id"] = sales["product_id"].astype(str)
        sales["date"] = pd.to_datetime(sales["date"], errors="coerce")
        sales["units_sold"] = pd.to_numeric(sales["units_sold"], errors="coerce").fillna(0).astype(int)
        sales["unit_selling_price"] = pd.to_numeric(sales["unit_selling_price"], errors="coerce").fillna(0.0)
        sales["discount_percent"] = pd.to_numeric(sales["discount_percent"], errors="coerce").fillna(0.0)
        sales["revenue"] = sales["units_sold"] * sales["unit_selling_price"]
        
    if not reviews.empty:
        reviews["product_id"] = reviews["product_id"].astype(str)
        reviews["rating"] = pd.to_numeric(reviews["rating"], errors="coerce").fillna(3).astype(int)
        reviews["review_text"] = reviews["review_text"].astype(str)
        reviews["review_date"] = pd.to_datetime(reviews["review_date"], errors="coerce")
        
    if not competitors.empty:
        competitors["product_id"] = competitors["product_id"].astype(str)
        competitors["competitor_price"] = pd.to_numeric(competitors["competitor_price"], errors="coerce").fillna(0.0)
        competitors["observed_date"] = pd.to_datetime(competitors["observed_date"], errors="coerce")
        
    return {
        "products": products,
        "sales": sales,
        "reviews": reviews,
        "competitors": competitors
    }


def get_dashboard_metrics(
    products_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    reviews_df: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    Compute aggregate portfolio KPIs across the retail catalog.
    All figures are derived strictly from raw data tables.
    """
    if products_df.empty:
        return {
            "total_revenue": 0.0,
            "total_gross_profit": 0.0,
            "total_units_sold": 0,
            "avg_rating": 0.0,
            "total_inventory": 0,
            "active_skus": 0,
            "overall_margin_pct": 0.0
        }
        
    active_skus = len(products_df)
    total_inventory = int(products_df["stock"].sum())
    
    # Calculate revenue and profit using sales merged with product unit cost
    total_revenue = 0.0
    total_gross_profit = 0.0
    total_units_sold = 0
    
    if not sales_df.empty:
        total_units_sold = int(sales_df["units_sold"].sum())
        total_revenue = float(sales_df["revenue"].sum())
        
        # Merge to associate unit cost per sale
        merged_sales = sales_df.merge(
            products_df[["product_id", "unit_cost"]],
            on="product_id",
            how="left"
        )
        merged_sales["unit_cost"] = merged_sales["unit_cost"].fillna(0.0)
        merged_sales["gross_profit"] = (
            merged_sales["units_sold"] * (merged_sales["unit_selling_price"] - merged_sales["unit_cost"])
        )
        total_gross_profit = float(merged_sales["gross_profit"].sum())
        
    overall_margin = (total_gross_profit / total_revenue * 100.0) if total_revenue > 0 else 0.0
    
    # Average catalog rating
    avg_rating = 0.0
    if reviews_df is not None and not reviews_df.empty and "rating" in reviews_df.columns:
        avg_rating = round(float(reviews_df["rating"].mean()), 2)
        
    return {
        "total_revenue": round(total_revenue, 2),
        "total_gross_profit": round(total_gross_profit, 2),
        "total_units_sold": total_units_sold,
        "avg_rating": avg_rating,
        "total_inventory": total_inventory,
        "active_skus": active_skus,
        "overall_margin_pct": round(overall_margin, 2)
    }


def get_sales_trend(sales_df: pd.DataFrame, product_id: Optional[str] = None) -> pd.DataFrame:
    """
    Compute daily sales volume and revenue trend.
    Optionally filters for a specific product SKU.
    """
    if sales_df.empty or "date" not in sales_df.columns:
        return pd.DataFrame(columns=["date", "units_sold", "revenue"])
        
    filtered = sales_df if product_id is None else sales_df[sales_df["product_id"] == product_id]
    
    if filtered.empty:
        return pd.DataFrame(columns=["date", "units_sold", "revenue"])
        
    trend = filtered.groupby("date").agg({
        "units_sold": "sum",
        "revenue": "sum"
    }).reset_index().sort_values("date")
    
    return trend


def get_product_performance(
    products_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    reviews_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Generate unified product-level performance matrix with sales, margins,
    ratings, and inventory status.
    """
    if products_df.empty:
        return pd.DataFrame()
        
    perf = products_df.copy()
    
    # Aggregate sales metrics
    if not sales_df.empty:
        sales_summary = sales_df.groupby("product_id").agg({
            "units_sold": "sum",
            "revenue": "sum"
        }).reset_index()
        perf = perf.merge(sales_summary, on="product_id", how="left")
    else:
        perf["units_sold"] = 0
        perf["revenue"] = 0.0
        
    perf["units_sold"] = perf["units_sold"].fillna(0).astype(int)
    perf["revenue"] = perf["revenue"].fillna(0.0)
    perf["total_gross_profit"] = perf["units_sold"] * (perf["selling_price"] - perf["unit_cost"])
    
    # Merge review ratings
    if reviews_df is not None and not reviews_df.empty:
        review_summary = reviews_df.groupby("product_id").agg({
            "rating": ["mean", "count"]
        })
        review_summary.columns = ["avg_rating", "review_count"]
        review_summary = review_summary.reset_index()
        review_summary["avg_rating"] = review_summary["avg_rating"].round(2)
        perf = perf.merge(review_summary, on="product_id", how="left")
    else:
        perf["avg_rating"] = 0.0
        perf["review_count"] = 0
        
    perf["avg_rating"] = perf["avg_rating"].fillna(0.0)
    perf["review_count"] = perf["review_count"].fillna(0).astype(int)
    
    # Classification: Best Performing vs Slow Moving
    # A product is classified as 'Best Performing' if revenue is above median,
    # and 'Slow Moving' if units sold are low or inventory age is high.
    median_revenue = perf["revenue"].median() if not perf.empty else 0
    perf["performance_tag"] = np.where(
        perf["revenue"] >= median_revenue,
        "High Velocity",
        np.where(perf["inventory_age_days"] >= 60, "Slow Moving / Aged", "Steady")
    )
    
    return perf
