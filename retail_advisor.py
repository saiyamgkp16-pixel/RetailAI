"""
retail_advisor.py - AI Retail Advisor and Interactive Business Consultant
Part of RetailPulse AI

Combines structured calculations from pricing_engine, discount_engine, and
analytics to empower an interactive AI advisor via NVIDIA NIM.
Features a robust deterministic offline fallback answering queries with verified facts.
"""

from typing import Dict, Any, Optional
import pandas as pd
from nvidia_client import ask_nvidia, get_nvidia_config
from pricing_engine import calculate_price_metrics
from discount_engine import recommend_discount, simulate_discount
from review_engine import analyze_reviews


def compile_product_context(
    product_id: str,
    products_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    reviews_df: pd.DataFrame,
    competitors_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Assemble complete, ground-truth business facts for a specific product.
    All figures are calculated by deterministic Python modules.
    """
    if products_df.empty or product_id not in products_df["product_id"].values:
        return {}
        
    p_row = products_df[products_df["product_id"] == product_id].iloc[0]
    
    # Financial & Pricing metrics
    price_metrics = calculate_price_metrics(p_row, competitors_df)
    
    # Review analysis
    review_analysis = analyze_reviews(product_id, reviews_df, use_ai=False)
    
    # Heuristic recommendation
    rec = recommend_discount(p_row, sales_df, reviews_df, competitors_df)
    
    # Standard discount simulation at 10%
    sim_10 = simulate_discount(
        selling_price=price_metrics["selling_price"],
        unit_cost=price_metrics["unit_cost"],
        target_margin=p_row["target_margin"],
        discount_percent=10.0
    )
    
    return {
        "product_id": product_id,
        "product_name": p_row["product_name"],
        "category": p_row.get("category", "General"),
        "purchase_cost": float(p_row["purchase_cost"]),
        "variable_cost": float(p_row["variable_cost"]),
        "unit_cost": price_metrics["unit_cost"],
        "selling_price": price_metrics["selling_price"],
        "unit_profit": price_metrics["unit_profit"],
        "margin_percent": price_metrics["margin_percent"],
        "markup_percent": price_metrics["markup_percent"],
        "target_margin_percent": price_metrics["target_margin_percent"],
        "minimum_price_for_target": price_metrics["minimum_price_for_target"],
        "stock": int(p_row["stock"]),
        "inventory_age_days": int(p_row["inventory_age_days"]),
        "competitor_median": price_metrics["competitor_median"],
        "competitor_count": price_metrics["competitor_count"],
        "average_rating": review_analysis["average_rating"],
        "total_reviews": review_analysis["total_reviews"],
        "positive_themes": review_analysis["positive_themes"],
        "negative_themes": review_analysis["negative_themes"],
        "common_complaints": review_analysis["common_complaints"],
        "action_type": rec["action_type"],
        "reasons": rec["reasons"],
        "sales_trend_direction": rec["sales_trend_direction"],
        "recent_units_sold": rec["recent_units_sold"],
        "max_allowable_discount": sim_10["max_allowable_discount_percent"],
        "sim_10_margin": sim_10["new_margin_percent"],
        "sim_10_target_maintained": sim_10["target_margin_maintained"]
    }


def generate_local_advisor_reply(query: str, ctx: Dict[str, Any]) -> str:
    """
    Deterministic rule-based retail advisor fallback.
    Answers common retailer questions grounded strictly in the product's verified facts.
    """
    if not ctx:
        return (
            "Please select a valid product SKU from the dropdown to allow RetailPulse AI "
            "to analyze pricing, customer reviews, and sales velocity."
        )
        
    q = query.lower()
    p_name = ctx["product_name"]
    p_id = ctx["product_id"]
    sp = ctx["selling_price"]
    cost = ctx["unit_cost"]
    margin = ctx["margin_percent"]
    target_margin = ctx["target_margin_percent"]
    stock = ctx["stock"]
    rating = ctx["average_rating"]
    trend = ctx["sales_trend_direction"]
    rec = ctx["action_type"]
    reasons = ctx["reasons"]
    
    # 1. Why are sales declining?
    if any(k in q for k in ["declin", "drop", "fall", "why sales", "decreasing"]):
        if ctx["common_complaints"] and ctx["common_complaints"] != ["None"]:
            complaints_str = ", ".join(ctx["common_complaints"])
            return (
                f"### Sales Analysis for {p_name} ({p_id})\n\n"
                f"Recent sales trend is **{trend}** with {ctx['recent_units_sold']} units sold in the last 14 days.\n\n"
                f"**Key Root Cause:** Customer satisfaction stands at **{rating:.1f}/5** with recurring complaints regarding **{complaints_str}**.\n\n"
                f"- **Verified Insight:** Negative reviews indicate buyers are experiencing hardware or functional friction rather than price resistance.\n"
                f"- **Stock Status:** You currently have **{stock} units** in inventory.\n"
                f"- **Strategic Recommendation:** {rec}\n\n"
                f"*Action Step:* Engage your supplier to inspect the current batch. Do not apply a blanket discount, as price reductions will not resolve quality grievances."
            )
        else:
            return (
                f"### Sales Trend Analysis for {p_name}\n\n"
                f"Sales velocity is **{trend}**. Rating remains positive at **{rating:.1f}/5** with current stock of **{stock} units**.\n"
                f"Current selling price is ₹{sp:,.2f} yielding a {margin:.1f}% gross margin. "
                f"Recommendation: {rec}"
            )
            
    # 2. Should I offer a discount?
    elif any(k in q for k in ["discount", "promotion", "promo", "offer", "sale"]):
        return (
            f"### Discount Advisory for {p_name} ({p_id})\n\n"
            f"**Recommendation:** **{rec}**\n\n"
            f"**Financial Rationale:**\n"
            f"- Current Selling Price: **₹{sp:,.2f}** | Total Unit Cost: **₹{cost:,.2f}**\n"
            f"- Current Gross Margin: **{margin:.1f}%** (Target: **{target_margin:.1f}%**)\n"
            f"- Maximum Allowable Discount to preserve target margin: **{ctx['max_allowable_discount']:.1f}%**\n"
            f"- On-hand Inventory: **{stock} units** (Inventory Age: **{ctx['inventory_age_days']} days**)\n\n"
            f"**Key Heuristic Reasons:**\n" +
            "\n".join([f"- {r}" for r in reasons]) +
            f"\n\n*Note:* If a 10% discount were tested, gross margin would adjust to {ctx['sim_10_margin']:.1f}%."
        )

    # 3. What are customers complaining about?
    elif any(k in q for k in ["complain", "review", "satisfaction", "customer say", "feedback"]):
        complaints_list = ctx["negative_themes"]
        praise_list = ctx["positive_themes"]
        return (
            f"### Customer Voice & Review Summary for {p_name}\n\n"
            f"- **Overall Rating:** **{rating:.1f} / 5.0** across {ctx['total_reviews']} verified reviews.\n\n"
            f"**What Customers Are Complaining About:**\n" +
            "\n".join([f"- {c}" for c in complaints_list]) +
            f"\n\n**What Customers Appreciate:**\n" +
            "\n".join([f"- {p}" for p in praise_list]) +
            f"\n\n**Retailer Takeaway:** Review sentiments demonstrate that customer retention depends on addressing the specific issues noted above."
        )

    # 4. Pricing & Margin questions
    elif any(k in q for k in ["price", "margin", "cost", "competitor", "markup"]):
        comp_info = (
            f"Competitor median price is **₹{ctx['competitor_median']:,.2f}** (across {ctx['competitor_count']} benchmark sources)."
            if ctx["competitor_median"] else "No competitor pricing currently logged."
        )
        return (
            f"### Pricing & Margin Breakdown for {p_name}\n\n"
            f"- **Selling Price:** ₹{sp:,.2f}\n"
            f"- **Unit Cost:** ₹{cost:,.2f} (Purchase: ₹{ctx['purchase_cost']:,.2f} + Variable: ₹{ctx['variable_cost']:,.2f})\n"
            f"- **Unit Profit:** ₹{ctx['unit_profit']:,.2f}\n"
            f"- **Gross Margin:** **{margin:.1f}%** vs Target **{target_margin:.1f}%**\n"
            f"- **Minimum Price for Target Margin:** ₹{ctx['minimum_price_for_target']:,.2f}\n"
            f"- **Market Benchmark:** {comp_info}\n\n"
            f"**Action:** {'Target margin is successfully achieved.' if margin >= target_margin else 'Price is below target margin requirement; evaluate price revision.'}"
        )

    # 5. Inventory & Attention questions
    elif any(k in q for k in ["stock", "inventory", "attention", "action", "slow"]):
        return (
            f"### Inventory Health Assessment for {p_name}\n\n"
            f"- **Stock On Hand:** **{stock} units**\n"
            f"- **Inventory Shelf Age:** **{ctx['inventory_age_days']} days**\n"
            f"- **Sales Velocity:** **{trend}**\n"
            f"- **Strategic Status:** **{rec}**\n\n"
            f"**Action Plan:**\n" +
            "\n".join([f"- {r}" for r in reasons])
        )

    # Default overview
    else:
        return (
            f"### Retail Executive Brief: {p_name} ({p_id})\n\n"
            f"- **Financials:** Selling at **₹{sp:,.2f}** with **{margin:.1f}% margin** (Unit Profit: ₹{ctx['unit_profit']:,.2f}).\n"
            f"- **Inventory:** **{stock} units** in stock (Shelf Age: {ctx['inventory_age_days']} days).\n"
            f"- **Customer Sentiment:** **{rating:.1f}/5** rating over {ctx['total_reviews']} reviews.\n"
            f"- **Primary Recommendation:** **{rec}**\n\n"
            f"You can ask me specific questions like:\n"
            f"- *'Why are sales of this product declining?'*\n"
            f"- *'Should I offer a discount on this product?'*\n"
            f"- *'What are customers complaining about?'*\n"
            f"- *'Is the current selling price appropriate?'*"
        )


def ask_retail_advisor(
    query: str,
    product_context: Dict[str, Any],
    catalog_summary: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main entrypoint for RetailPulse AI natural-language assistant.
    Attempts NVIDIA NIM LLM invocation with strict metric grounding.
    Falls back gracefully to local deterministic advisor if offline.
    """
    if not product_context:
        return {
            "answer": "Please select a product SKU from the sidebar or product dropdown to begin analysis.",
            "source": "System",
            "model": "None"
        }
        
    config = get_nvidia_config()
    
    if config["is_configured"]:
        system_prompt = (
            "You are RetailPulse AI Advisor, an expert retail intelligence consultant advising shop owners.\n"
            "CRITICAL ARCHITECTURAL CONSTRAINTS:\n"
            "1. Base your answer EXCLUSIVELY on the verified product metrics, calculations, and customer reviews supplied below.\n"
            "2. NEVER invent, calculate, or hallucinate different financial figures, prices, margins, or stock counts.\n"
            "3. Reference exact numbers (₹ currency, % margin, units sold) from the context.\n"
            "4. Clearly distinguish between actual data, calculated scenarios, and strategic advice.\n"
            "5. Never claim that a discount or price cut guarantees an increase in sales.\n"
            "6. Keep your response professional, concise, structured with Markdown headers and bullet points."
        )
        
        ctx_summary = f"""
VERIFIED PRODUCT DATA (Calculated by Python Engine):
- Product ID: {product_context['product_id']}
- Product Name: {product_context['product_name']}
- Category: {product_context['category']}
- Purchase Cost: ₹{product_context['purchase_cost']:,.2f}
- Variable Cost: ₹{product_context['variable_cost']:,.2f}
- Total Unit Cost: ₹{product_context['unit_cost']:,.2f}
- Current Selling Price: ₹{product_context['selling_price']:,.2f}
- Current Unit Profit: ₹{product_context['unit_profit']:,.2f}
- Current Gross Margin: {product_context['margin_percent']:.1f}%
- Target Gross Margin: {product_context['target_margin_percent']:.1f}%
- Minimum Selling Price for Target Margin: ₹{product_context['minimum_price_for_target']:,.2f}
- On-hand Stock: {product_context['stock']} units
- Inventory Shelf Age: {product_context['inventory_age_days']} days
- Recent Sales Velocity (14-day): {product_context['recent_units_sold']} units ({product_context['sales_trend_direction']})
- Average Customer Rating: {product_context['average_rating']:.1f}/5 across {product_context['total_reviews']} reviews
- Competitor Median Price: ₹{product_context['competitor_median']:,.2f} (if available)
- Top Common Complaints: {", ".join(product_context['common_complaints'])}
- Top Positive Feedback: {", ".join(product_context['positive_themes'])}
- Rule-based Suggested Action: {product_context['action_type']}
- Heuristic Reasons: {" | ".join(product_context['reasons'])}
"""
        prompt = f"{ctx_summary}\n\nRetailer Question: {query}\n\nProvide an insightful, explainable business answer."
        
        ai_resp = ask_nvidia(prompt, system_prompt=system_prompt, max_tokens=850, temperature=0.2)
        if ai_resp["success"] and ai_resp["content"]:
            return {
                "answer": ai_resp["content"],
                "source": f"NVIDIA NIM ({config['model']})",
                "model": config["model"]
            }
            
    # Deterministic Local Fallback
    local_reply = generate_local_advisor_reply(query, product_context)
    return {
        "answer": local_reply,
        "source": "Local Deterministic Heuristic Advisor (Offline Fallback)",
        "model": "Rule-Based Python Engine"
    }
