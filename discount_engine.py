"""
discount_engine.py - Interactive Discount Simulator and Business Recommendation Engine
Part of RetailPulse AI

Implements mathematical discount scenario analysis and multi-factor heuristic
pricing recommendations based on sales velocity, inventory age, stock, customer sentiment,
and competitor benchmarking.
"""

from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
from pricing_engine import calculate_unit_cost, calculate_minimum_price


def simulate_discount(
    selling_price: float,
    unit_cost: float,
    target_margin: float,
    discount_percent: float
) -> Dict[str, Any]:
    """
    Simulate the financial impact of a proposed discount percentage.
    
    Required Calculations:
        Discounted price = Current price * (1 - Discount percentage / 100)
        Discount amount = Current price - Discounted price
        New unit profit = Discounted price - Unit cost
        New gross margin (%) = (New unit profit / Discounted price) * 100
        Profit difference per unit = New unit profit - Current unit profit
        
        Required sales volume uplift to maintain previous total gross profit:
        Uplift (%) = ((Current unit profit / Discounted unit profit) - 1) * 100
        
        Maximum discount allowed while maintaining target margin:
        Max Discount (%) = max(0.0, (1 - (Minimum target price / Current price))) * 100
    """
    sp = float(selling_price)
    cost = float(unit_cost)
    disc_pct = float(discount_percent)
    
    current_profit = round(sp - cost, 2)
    current_margin = round((current_profit / sp * 100.0) if sp > 0 else 0.0, 2)
    
    # Calculate discounted figures
    discount_multiplier = 1.0 - (disc_pct / 100.0)
    discounted_price = round(sp * discount_multiplier, 2)
    discount_amount = round(sp - discounted_price, 2)
    new_unit_profit = round(discounted_price - cost, 2)
    
    if discounted_price > 0:
        new_margin = round((new_unit_profit / discounted_price) * 100.0, 2)
    else:
        new_margin = 0.0
        
    profit_diff = round(new_unit_profit - current_profit, 2)
    
    # Target margin evaluation
    tgt_margin_decimal = target_margin / 100.0 if target_margin > 1.0 else target_margin
    target_margin_pct = round(tgt_margin_decimal * 100.0, 2)
    target_maintained = new_margin >= target_margin_pct
    
    # Minimum price required for target margin
    try:
        min_target_price = calculate_minimum_price(cost, tgt_margin_decimal)
        if sp > min_target_price and sp > 0:
            max_allowable_discount = round((1.0 - (min_target_price / sp)) * 100.0, 2)
        else:
            max_allowable_discount = 0.0
    except ValueError:
        min_target_price = cost
        max_allowable_discount = 0.0
        
    # Required sales volume uplift calculation
    uplift_percentage = None
    uplift_feasible = False
    uplift_explanation = ""
    
    if disc_pct == 0.0:
        uplift_percentage = 0.0
        uplift_feasible = True
        uplift_explanation = "At 0% discount, zero additional volume is required to maintain total gross profit."
    elif current_profit > 0 and new_unit_profit > 0:
        uplift = ((current_profit / new_unit_profit) - 1.0) * 100.0
        uplift_percentage = round(uplift, 1)
        uplift_feasible = True
        uplift_explanation = (
            f"To maintain your prior total gross profit, you would need to sell "
            f"+{uplift_percentage:.1f}% more units (from 100 units to ~{int(round(100 * (1 + uplift/100)))} units). "
            f"Note: This is a mathematical scenario, not a guarantee that demand will expand."
        )
    elif new_unit_profit <= 0:
        uplift_percentage = None
        uplift_feasible = False
        uplift_explanation = (
            "CRITICAL WARNING: The discounted selling price is at or below unit cost. "
            "No increase in sales volume can ever recover the lost gross profit because every unit sold yields zero or negative return."
        )
    else:
        uplift_percentage = None
        uplift_feasible = False
        uplift_explanation = "Current profit base is non-positive; break-even uplift cannot be meaningfully computed."
        
    return {
        "current_price": sp,
        "discount_percent": disc_pct,
        "discounted_price": discounted_price,
        "discount_amount": discount_amount,
        "unit_cost": cost,
        "current_unit_profit": current_profit,
        "current_margin_percent": current_margin,
        "new_unit_profit": new_unit_profit,
        "new_margin_percent": new_margin,
        "profit_difference_per_unit": profit_diff,
        "target_margin_percent": target_margin_pct,
        "target_margin_maintained": target_maintained,
        "minimum_target_price": min_target_price,
        "max_allowable_discount_percent": max_allowable_discount,
        "required_volume_uplift_percent": uplift_percentage,
        "uplift_feasible": uplift_feasible,
        "uplift_explanation": uplift_explanation
    }


def recommend_discount(
    product: Dict[str, Any] | pd.Series,
    sales_df: Optional[pd.DataFrame] = None,
    reviews_df: Optional[pd.DataFrame] = None,
    competitor_df: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    Generate an explainable, multi-factor business recommendation on pricing and discounting.
    
    Considers:
        - 30-day sales velocity and trend
        - Stock level and inventory coverage
        - Inventory age (days)
        - Customer satisfaction (rating and review complaints)
        - Current profit margin cushion
        - Competitor pricing benchmark
    """
    p_id = product.get("product_id")
    p_name = product.get("product_name", "")
    sp = float(product.get("selling_price", 0.0))
    purchase_cost = float(product.get("purchase_cost", 0.0))
    variable_cost = float(product.get("variable_cost", 0.0))
    unit_cost = calculate_unit_cost(purchase_cost, variable_cost)
    stock = int(product.get("stock", 0))
    inv_age = int(product.get("inventory_age_days", 0))
    target_margin = float(product.get("target_margin", 0.30))
    target_margin_pct = target_margin * 100.0 if target_margin <= 1.0 else target_margin
    current_profit = sp - unit_cost
    current_margin_pct = (current_profit / sp * 100.0) if sp > 0 else 0.0

    # 1. Sales Velocity & Trend Analysis
    sales_trend_direction = "Stable"
    recent_units_sold = 0
    prior_units_sold = 0
    sales_velocity_status = "Low"
    
    if sales_df is not None and not sales_df.empty and "product_id" in sales_df.columns:
        p_sales = sales_df[sales_df["product_id"] == p_id].copy()
        if not p_sales.empty and "units_sold" in p_sales.columns:
            p_sales["date"] = pd.to_datetime(p_sales["date"])
            p_sales = p_sales.sort_values("date")
            
            # Split into recent 14 days vs prior 14 days if sufficient records exist
            max_date = p_sales["date"].max()
            split_date = max_date - pd.Timedelta(days=14)
            
            recent_sales = p_sales[p_sales["date"] > split_date]
            prior_sales = p_sales[p_sales["date"] <= split_date]
            
            recent_units_sold = int(recent_sales["units_sold"].sum())
            prior_units_sold = int(prior_sales["units_sold"].sum()) if not prior_sales.empty else recent_units_sold
            
            if recent_units_sold < (prior_units_sold * 0.65) and prior_units_sold > 5:
                sales_trend_direction = "Declining"
            elif recent_units_sold > (prior_units_sold * 1.35):
                sales_trend_direction = "Growing"
            else:
                sales_trend_direction = "Stable"
                
            if recent_units_sold > 50:
                sales_velocity_status = "High"
            elif recent_units_sold < 10:
                sales_velocity_status = "Low"
            else:
                sales_velocity_status = "Moderate"

    # 2. Customer Satisfaction Analysis
    avg_rating = 0.0
    review_count = 0
    recurring_complaints = []
    
    if reviews_df is not None and not reviews_df.empty and "product_id" in reviews_df.columns:
        p_reviews = reviews_df[reviews_df["product_id"] == p_id]
        if not p_reviews.empty:
            avg_rating = round(float(p_reviews["rating"].mean()), 2)
            review_count = len(p_reviews)
            
            # Simple keyword scan for recurring defects
            low_reviews = p_reviews[p_reviews["rating"] <= 3]["review_text"].str.lower().tolist()
            text_corpus = " ".join(low_reviews)
            for keyword in ["battery", "charging", "strap", "zipper", "leak", "damp", "heat", "broken", "app"]:
                if keyword in text_corpus:
                    recurring_complaints.append(keyword)

    # 3. Competitor Benchmark Analysis
    competitor_median = None
    if competitor_df is not None and not competitor_df.empty and "product_id" in competitor_df.columns:
        p_comps = competitor_df[competitor_df["product_id"] == p_id]
        if not p_comps.empty and "competitor_price" in p_comps.columns:
            prices = p_comps["competitor_price"].dropna()
            if not prices.empty:
                competitor_median = float(prices.median())

    # 4. Multi-Factor Heuristic Evaluation
    reasons: List[str] = []
    action_type = "Maintain current price."
    urgency = "Normal"
    suggested_discount_range = "0%"

    # Rule A: Poor Customer Satisfaction / Recurring Complaints (HIGHEST PRIORITY)
    if (avg_rating > 0 and avg_rating < 3.5) or len(recurring_complaints) > 0:
        action_type = "Investigate product quality or customer complaints first."
        urgency = "High"
        suggested_discount_range = "0% (Avoid discount)"
        reasons.append(
            f"Average customer rating is {avg_rating:.1f}/5 with {review_count} reviews. "
            f"Recurring complaints detected regarding: {', '.join(set(recurring_complaints)) if recurring_complaints else 'product durability'}."
        )
        reasons.append(
            "Customer friction is driven by quality/defects rather than price resistance. "
            "Applying a discount will erode margins while failing to resolve product returns or dissatisfaction."
        )
        reasons.append("Immediate Action: Inspect incoming batch with the supplier, pause heavy marketing, and address warranty requests.")

    # Rule B: Fast Moving / High Sales Velocity and Low Stock
    elif (sales_velocity_status == "High" or sales_trend_direction == "Growing") and stock <= 20:
        action_type = "Avoid an unnecessary discount."
        urgency = "Moderate"
        suggested_discount_range = "0%"
        reasons.append(f"High sales velocity ({recent_units_sold} units recently) paired with low inventory ({stock} units remaining).")
        reasons.append("Demand is robust; discounting would prematurely deplete stock without capturing available gross margin.")
        reasons.append("Immediate Action: Initiate a stock replenishment reorder; maintain full price to maximize profitability.")

    # Rule C: Aged Inventory & Stagnant Demand (Clearance Markdown)
    elif inv_age >= 60 and (sales_velocity_status == "Low" or sales_trend_direction == "Declining"):
        action_type = "Consider a phased markdown for slow-moving or old inventory."
        urgency = "High"
        suggested_discount_range = "10% - 20%"
        reasons.append(f"Inventory age is {inv_age} days (exceeds 60-day shelf threshold) with low velocity ({recent_units_sold} units sold).")
        reasons.append("Working capital and storage space are locked up in stagnant stock.")
        reasons.append("Immediate Action: Initiate a phased clearance promotion (start at 10-15%) to liquidate units before depreciation.")

    # Rule D: Declining Sales with Excess Stock and Satisfied Customers (Promotional Candidate)
    elif sales_trend_direction == "Declining" and stock > 50 and avg_rating >= 3.8:
        action_type = "Consider a small controlled promotion."
        urgency = "Moderate"
        suggested_discount_range = "5% - 12%"
        reasons.append(f"Sales volume has declined while stock remains elevated ({stock} units in warehouse).")
        reasons.append(f"Customer satisfaction is strong ({avg_rating:.1f}/5), indicating product quality is not the root issue.")
        reasons.append(
            f"Current gross margin of {current_margin_pct:.1f}% provides adequate headroom above the {target_margin_pct:.1f}% target."
        )
        reasons.append("Immediate Action: Test a limited-time 5-10% weekend bundle or promotion to stimulate velocity.")

    # Rule E: Competitor Price Disadvantage
    elif competitor_median and sp > (competitor_median * 1.15) and avg_rating < 4.5:
        action_type = "Review competitor positioning."
        urgency = "Moderate"
        suggested_discount_range = "5% - 10%"
        reasons.append(f"Current selling price (₹{sp:,.2f}) is substantially higher than the competitor median (₹{competitor_median:,.2f}).")
        reasons.append("Price discrepancy may be causing customer migration to competing platforms.")
        reasons.append("Immediate Action: Evaluate competitor product specifications and consider tactical price alignment.")

    # Rule F: Healthy Baseline
    else:
        action_type = "Maintain current price."
        urgency = "Low"
        suggested_discount_range = "0%"
        reasons.append(f"Sales velocity is {sales_velocity_status.lower()} and customer satisfaction is solid ({avg_rating:.1f}/5).")
        reasons.append(f"Current gross profit margin ({current_margin_pct:.1f}%) meets or exceeds operational objectives.")
        reasons.append("Inventory levels ({stock} units) are well-calibrated to current demand. No price interventions required.")

    return {
        "product_id": p_id,
        "product_name": p_name,
        "action_type": action_type,
        "urgency": urgency,
        "suggested_discount_range": suggested_discount_range,
        "reasons": reasons,
        "sales_trend_direction": sales_trend_direction,
        "sales_velocity_status": sales_velocity_status,
        "recent_units_sold": recent_units_sold,
        "stock": stock,
        "inventory_age_days": inv_age,
        "average_rating": avg_rating,
        "review_count": review_count,
        "recurring_complaints": list(set(recurring_complaints)),
        "current_margin_percent": round(current_margin_pct, 2),
        "target_margin_percent": round(target_margin_pct, 2),
        "competitor_median": competitor_median
    }
