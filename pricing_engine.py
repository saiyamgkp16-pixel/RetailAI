"""
pricing_engine.py - Deterministic Financial and Pricing Calculations
Part of RetailPulse AI

All financial computations, margins, markups, and target price requirements
are strictly implemented in Python/NumPy to prevent LLM hallucinations.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np


def calculate_unit_cost(purchase_cost: float, variable_cost: float = 0.0) -> float:
    """
    Calculate the total unit cost.
    Formula: Unit cost = Purchase cost + Additional variable cost per unit
    """
    return round(float(purchase_cost) + float(variable_cost), 2)


def calculate_unit_profit(selling_price: float, unit_cost: float) -> float:
    """
    Calculate unit profit (contribution before fixed overhead).
    Formula: Unit profit = Selling price - Unit cost
    """
    return round(float(selling_price) - float(unit_cost), 2)


def calculate_margin(selling_price: float, unit_cost: float) -> Dict[str, float]:
    """
    Calculate gross profit margin percentage and markup percentage.
    
    Formulas:
        Unit profit = Selling price - Unit cost
        Gross margin (%) = (Unit profit / Selling price) * 100
        Markup (%) = (Unit profit / Unit cost) * 100
    """
    sp = float(selling_price)
    cost = float(unit_cost)
    profit = calculate_unit_profit(sp, cost)
    
    # Margin guard: avoid division by zero or negative price
    if sp > 0:
        margin_pct = (profit / sp) * 100.0
    else:
        margin_pct = 0.0
        
    # Markup guard: avoid division by zero if cost is zero
    if cost > 0:
        markup_pct = (profit / cost) * 100.0
    else:
        markup_pct = 0.0
        
    return {
        "unit_cost": round(cost, 2),
        "selling_price": round(sp, 2),
        "unit_profit": round(profit, 2),
        "margin_percent": round(margin_pct, 2),
        "markup_percent": round(markup_pct, 2)
    }


def calculate_minimum_price(unit_cost: float, target_margin: float) -> float:
    """
    Calculate the minimum selling price required to achieve a target gross margin.
    
    Formula:
        Minimum price = Unit cost / (1 - Target margin decimal)
        
    Example:
        Unit cost = ₹1,000, Target margin = 20% (0.20)
        Minimum price = 1000 / (1 - 0.20) = 1000 / 0.80 = ₹1,250
        Check: (1250 - 1000) / 1250 = 250 / 1250 = 20%
    """
    cost = float(unit_cost)
    margin = float(target_margin)
    
    # Guardrails
    if margin < 0.0:
        raise ValueError("Target margin cannot be negative.")
    if margin == 1.0 or margin >= 100.0:
        raise ValueError("Target margin must be less than 100% (1.0).")
        
    # Normalize percentage if passed as e.g. 20 instead of 0.20
    if margin > 1.0:
        margin = margin / 100.0
        
    if margin >= 1.0:
        raise ValueError("Target margin must be less than 100% (1.0).")
        
    min_price = cost / (1.0 - margin)
    return round(min_price, 2)


def calculate_price_metrics(product: Dict[str, Any] | pd.Series, 
                            competitor_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Compute comprehensive pricing health metrics for a selected product,
    including target margin feasibility and competitor median benchmarking.
    """
    p_id = product.get("product_id")
    purchase_cost = float(product.get("purchase_cost", 0.0))
    variable_cost = float(product.get("variable_cost", 0.0))
    selling_price = float(product.get("selling_price", 0.0))
    target_margin = float(product.get("target_margin", 0.30))
    
    unit_cost = calculate_unit_cost(purchase_cost, variable_cost)
    base_metrics = calculate_margin(selling_price, unit_cost)
    
    try:
        min_price_target = calculate_minimum_price(unit_cost, target_margin)
    except ValueError:
        min_price_target = unit_cost
        
    target_margin_pct = target_margin * 100.0 if target_margin <= 1.0 else target_margin
    margin_achieved = base_metrics["margin_percent"] >= target_margin_pct
    
    # Competitor Benchmark Analysis
    competitor_median = None
    competitor_diff = None
    competitor_count = 0
    
    if competitor_df is not None and not competitor_df.empty and "product_id" in competitor_df.columns:
        p_comps = competitor_df[competitor_df["product_id"] == p_id]
        if not p_comps.empty and "competitor_price" in p_comps.columns:
            prices = p_comps["competitor_price"].dropna()
            if not prices.empty:
                competitor_median = round(float(prices.median()), 2)
                competitor_diff = round(selling_price - competitor_median, 2)
                competitor_count = len(prices)
                
    # Suggested Pricing Action based on deterministic rules
    pricing_action = "Price is balanced with current cost and margin targets."
    if not margin_achieved:
        pricing_action = (
            f"WARNING: Current selling price (₹{selling_price:,.2f}) is below the minimum price "
            f"(₹{min_price_target:,.2f}) required to achieve your {target_margin_pct:.1f}% target margin."
        )
    elif competitor_median and selling_price > (competitor_median * 1.15):
        pricing_action = (
            f"Price is ₹{competitor_diff:,.2f} higher than competitor median (₹{competitor_median:,.2f}). "
            f"Monitor conversion velocity unless premium brand positioning is established."
        )
    elif competitor_median and selling_price < (competitor_median * 0.90):
        pricing_action = (
            f"Price is ₹{abs(competitor_diff):,.2f} lower than competitor median (₹{competitor_median:,.2f}). "
            f"Opportunity exists to raise price toward ₹{competitor_median:,.2f} to expand gross margin."
        )
        
    return {
        "product_id": p_id,
        "product_name": product.get("product_name", ""),
        "unit_cost": unit_cost,
        "selling_price": selling_price,
        "unit_profit": base_metrics["unit_profit"],
        "margin_percent": base_metrics["margin_percent"],
        "markup_percent": base_metrics["markup_percent"],
        "target_margin_percent": round(target_margin_pct, 2),
        "minimum_price_for_target": min_price_target,
        "target_margin_achieved": margin_achieved,
        "competitor_median": competitor_median,
        "competitor_diff": competitor_diff,
        "competitor_count": competitor_count,
        "pricing_action": pricing_action
    }
