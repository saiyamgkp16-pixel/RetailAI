"""
app.py - RetailPulse AI Main Streamlit Dashboard Application
Intelligent Retail Pricing, Discount & Customer Satisfaction Intelligence System

Built for retail store owners and merchandisers to make data-backed pricing,
promotional, and operational decisions.
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

# Import internal business logic modules
from analytics import (
    load_all_data,
    get_dashboard_metrics,
    get_sales_trend,
    get_product_performance,
)
from pricing_engine import (
    calculate_unit_cost,
    calculate_margin,
    calculate_minimum_price,
    calculate_price_metrics,
)
from discount_engine import simulate_discount, recommend_discount
from review_engine import analyze_reviews
from nvidia_client import get_nvidia_config, check_nvidia_connection
from retail_advisor import compile_product_context, ask_retail_advisor

# Load environment configuration
load_dotenv()

# Streamlit Page Setup
st.set_page_config(
    page_title="RetailPulse AI | Retail Intelligence System",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Professional Retail Dashboard
st.markdown("""
<style>
    /* Metric Card Styling */
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        border-left: 5px solid #1f77b4;
        margin-bottom: 12px;
    }
    .metric-title {
        font-size: 0.82rem;
        text-transform: uppercase;
        color: #6c757d;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #212529;
    }
    .metric-subtitle {
        font-size: 0.8rem;
        color: #28a745;
        font-weight: 500;
        margin-top: 4px;
    }
    /* Recommendation Alert Boxes */
    .rec-box-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-left: 6px solid #ffc107;
        padding: 18px 20px;
        border-radius: 8px;
        margin: 14px 0;
    }
    .rec-box-danger {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-left: 6px solid #dc3545;
        padding: 18px 20px;
        border-radius: 8px;
        margin: 14px 0;
    }
    .rec-box-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-left: 6px solid #28a745;
        padding: 18px 20px;
        border-radius: 8px;
        margin: 14px 0;
    }
    .rec-box-info {
        background-color: #e2f0fb;
        border: 1px solid #b8daff;
        border-left: 6px solid #007bff;
        padding: 18px 20px;
        border-radius: 8px;
        margin: 14px 0;
    }
    /* Status Badge */
    .badge-online {
        display: inline-block;
        padding: 4px 10px;
        font-size: 0.78rem;
        font-weight: 600;
        border-radius: 12px;
        background-color: #d4edda;
        color: #155724;
    }
    .badge-offline {
        display: inline-block;
        padding: 4px 10px;
        font-size: 0.78rem;
        font-weight: 600;
        border-radius: 12px;
        background-color: #fff3cd;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)


# Load Datasets (Cached for Performance)
@st.cache_data
def load_datasets():
    return load_all_data("data")


datasets = load_datasets()
products_df = datasets["products"]
sales_df = datasets["sales"]
reviews_df = datasets["reviews"]
competitors_df = datasets["competitors"]

# Check NVIDIA Configuration Status
nvidia_cfg = get_nvidia_config()

# -------------------------------------------------------------
# SIDEBAR NAVIGATION & SYSTEM STATUS
# -------------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3081/3081559.png", width=60)
    st.title("RetailPulse AI")
    st.caption("Intelligent Pricing & Customer Intelligence")
    
    st.markdown("---")
    page = st.radio(
        "Navigation Modules:",
        [
            "📊 1. Retail Overview",
            "⭐ 2. Product Satisfaction",
            "🏷️ 3. Smart Pricing & Discount",
            "🤖 4. AI Retail Advisor"
        ],
        index=0
    )
    
    st.markdown("---")
    st.subheader("System Status")
    if nvidia_cfg["is_configured"]:
        st.markdown(
            f'<div class="badge-online">🟢 NVIDIA NIM Online</div><br/>'
            f'<small style="color:#6c757d;">Model: <code>{nvidia_cfg["model"].split("/")[-1]}</code></small>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="badge-offline">🟡 Local Fallback Mode</div><br/>'
            f'<small style="color:#6c757d;">NVIDIA API Key not configured. Using deterministic offline engines.</small>',
            unsafe_allow_html=True
        )
        
    st.markdown("---")
    st.caption("RetailPulse AI v1.0.0 | B.Tech CSE AI & ML Mini-Project")
    st.caption("Note: All financial metrics calculated deterministically in Python.")


# Helper: Product Selection Dropdown
def render_product_selector(key_prefix: str) -> str:
    options = {}
    for _, row in products_df.iterrows():
        label = f"{row['product_id']} — {row['product_name']} (Stock: {row['stock']} | ₹{row['selling_price']:,.0f})"
        options[row['product_id']] = label
        
    selected_id = st.selectbox(
        "Select Product to Analyze:",
        options=list(options.keys()),
        format_func=lambda pid: options[pid],
        key=f"{key_prefix}_product_select"
    )
    return selected_id


# =============================================================
# MODULE 1: RETAIL OVERVIEW DASHBOARD
# =============================================================
if page == "📊 1. Retail Overview":
    st.title("📊 Retail Overview Dashboard")
    st.markdown("High-level executive overview of sales, gross profit, inventory status, and customer sentiment across all product lines.")

    # Calculate Global Portfolio Metrics
    metrics = get_dashboard_metrics(products_df, sales_df, reviews_df)
    
    # KPI Cards Row
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    with kpi1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Revenue</div>
            <div class="metric-value">₹{metrics['total_revenue']:,.2f}</div>
            <div class="metric-subtitle">Across {metrics['active_skus']} SKUs</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi2:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #28a745;">
            <div class="metric-title">Total Gross Profit</div>
            <div class="metric-value">₹{metrics['total_gross_profit']:,.2f}</div>
            <div class="metric-subtitle">{metrics['overall_margin_pct']:.1f}% Avg Gross Margin</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi3:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #17a2b8;">
            <div class="metric-title">Total Units Sold</div>
            <div class="metric-value">{metrics['total_units_sold']:,}</div>
            <div class="metric-subtitle">Past 40 Days Sales</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi4:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #ffc107;">
            <div class="metric-title">Average Rating</div>
            <div class="metric-value">{metrics['avg_rating']:.1f} / 5.0 ⭐</div>
            <div class="metric-subtitle">From Customer Reviews</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi5:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #6f42c1;">
            <div class="metric-title">Warehouse Stock</div>
            <div class="metric-value">{metrics['total_inventory']:,} units</div>
            <div class="metric-subtitle">On-hand Inventory</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Visualizations Row 1: Sales Trend & Product Performance
    col_chart1, col_chart2 = st.columns([6, 5])
    
    with col_chart1:
        st.subheader("📈 Overall Sales Trend Over Time")
        trend_df = get_sales_trend(sales_df)
        if not trend_df.empty:
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(
                x=trend_df["date"],
                y=trend_df["revenue"],
                name="Daily Revenue (₹)",
                marker_color="#1f77b4",
                opacity=0.7
            ))
            fig_trend.add_trace(go.Scatter(
                x=trend_df["date"],
                y=trend_df["units_sold"],
                name="Units Sold",
                yaxis="y2",
                mode="lines+markers",
                line=dict(color="#ff7f0e", width=2.5)
            ))
            fig_trend.update_layout(
                yaxis=dict(title="Revenue (₹)"),
                yaxis2=dict(title="Units Sold", overlaying="y", side="right"),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=30, b=20),
                height=350
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No sales trend data available.")
            
    with col_chart2:
        st.subheader("📊 Product-wise Revenue & Gross Profit")
        perf_df = get_product_performance(products_df, sales_df, reviews_df)
        if not perf_df.empty:
            fig_bar = px.bar(
                perf_df,
                x="product_name",
                y=["revenue", "total_gross_profit"],
                barmode="group",
                labels={"value": "Amount (₹)", "product_name": "Product"},
                color_discrete_map={"revenue": "#1f77b4", "total_gross_profit": "#2ca02c"},
                title=""
            )
            fig_bar.update_layout(
                legend=dict(title="", orientation="h", y=1.1, x=0),
                xaxis=dict(tickangle=-25),
                margin=dict(l=20, r=20, t=30, b=20),
                height=350
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    # Visualizations Row 2: Profit Margins & Inventory Health
    col_chart3, col_chart4 = st.columns([5, 5])
    
    with col_chart3:
        st.subheader("🎯 Profit Margin Comparison vs Target")
        if not perf_df.empty:
            perf_df["target_margin_pct"] = perf_df["target_margin"] * 100
            fig_margin = go.Figure()
            fig_margin.add_trace(go.Bar(
                x=perf_df["product_name"],
                y=perf_df["margin_pct"],
                name="Current Margin %",
                marker_color="#2ca02c"
            ))
            fig_margin.add_trace(go.Scatter(
                x=perf_df["product_name"],
                y=perf_df["target_margin_pct"],
                name="Target Margin %",
                mode="lines+markers",
                line=dict(color="#d62728", width=3, dash="dot")
            ))
            fig_margin.update_layout(
                yaxis=dict(title="Margin Percentage (%)"),
                legend=dict(orientation="h", y=1.1, x=0),
                xaxis=dict(tickangle=-25),
                margin=dict(l=20, r=20, t=30, b=20),
                height=330
            )
            st.plotly_chart(fig_margin, use_container_width=True)

    with col_chart4:
        st.subheader("📦 Inventory Stock vs Shelf Age")
        if not perf_df.empty:
            fig_inv = px.scatter(
                perf_df,
                x="inventory_age_days",
                y="stock",
                size="units_sold",
                color="performance_tag",
                hover_name="product_name",
                labels={
                    "inventory_age_days": "Inventory Age (Days on Shelf)",
                    "stock": "Stock Units Remaining",
                    "performance_tag": "Velocity Status"
                },
                color_discrete_map={
                    "High Velocity": "#28a745",
                    "Steady": "#17a2b8",
                    "Slow Moving / Aged": "#dc3545"
                }
            )
            fig_inv.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                height=330
            )
            st.plotly_chart(fig_inv, use_container_width=True)

    # Catalog Summary Table
    st.markdown("---")
    st.subheader("📋 Comprehensive Product Performance Summary")
    display_table = perf_df[[
        "product_id", "product_name", "category", "selling_price",
        "units_sold", "revenue", "margin_pct", "stock", "inventory_age_days",
        "avg_rating", "performance_tag"
    ]].copy()
    display_table.columns = [
        "ID", "Product Name", "Category", "Selling Price (₹)",
        "Units Sold", "Revenue (₹)", "Margin %", "Stock", "Age (Days)",
        "Rating ⭐", "Status"
    ]
    st.dataframe(
        display_table.style.format({
            "Selling Price (₹)": "₹{:,.2f}",
            "Revenue (₹)": "₹{:,.2f}",
            "Margin %": "{:.1f}%",
            "Rating ⭐": "{:.2f}"
        }),
        use_container_width=True
    )


# =============================================================
# MODULE 2: PRODUCT SATISFACTION INTELLIGENCE
# =============================================================
elif page == "⭐ 2. Product Satisfaction":
    st.title("⭐ Product Satisfaction Intelligence")
    st.markdown("Analyze real customer reviews, surface recurring defects or complaints, and receive practical retailer suggestions.")

    # Product Selector
    selected_pid = render_product_selector("m2")
    p_info = products_df[products_df["product_id"] == selected_pid].iloc[0]

    # Run Review Analysis
    with st.spinner("Analyzing customer reviews..."):
        review_data = analyze_reviews(selected_pid, reviews_df, use_ai=True)

    st.markdown("---")

    # Header Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Product SKU", p_info["product_id"], p_info["category"])
    with c2:
        rating_color = "🟢" if review_data["average_rating"] >= 4.0 else ("🟡" if review_data["average_rating"] >= 3.5 else "🔴")
        st.metric("Average Rating", f"{rating_color} {review_data['average_rating']:.1f} / 5.0")
    with c3:
        st.metric("Total Reviews Analyzed", f"{review_data['total_reviews']} verified reviews")
    with c4:
        st.metric("Analysis Engine", review_data["source"])

    st.markdown("---")

    # Qualitative Themes (Positive vs Negative)
    col_pos, col_neg = st.columns(2)

    with col_pos:
        st.subheader("👍 Positive Feedback Themes")
        for item in review_data["positive_themes"]:
            st.success(f"✔ **{item}**")

    with col_neg:
        st.subheader("⚠️ Negative Feedback & Customer Pain Points")
        for item in review_data["negative_themes"]:
            st.error(f"✖ **{item}**")

    st.markdown("---")

    # Common Complaints & Executive Summary
    col_sum1, col_sum2 = st.columns([6, 5])

    with col_sum1:
        st.subheader("🚨 Recurring Customer Complaints")
        if review_data["common_complaints"] and review_data["common_complaints"] != ["None"]:
            for complaint in review_data["common_complaints"]:
                st.warning(f"**Identified Friction Area:** {complaint}")
        else:
            st.info("No critical recurring complaints identified in the customer reviews.")

        st.subheader("📝 Customer Satisfaction Executive Summary")
        st.info(review_data["summary"])

    with col_sum2:
        st.subheader("🛠️ Suggested Retailer Operational Actions")
        for action in review_data["suggested_actions"]:
            st.markdown(f"- 🔧 **{action}**")

        st.markdown("""
        > [!NOTE]
        > **Retail Rule:** When customer complaints indicate product quality defects (e.g. battery failure or leaks), 
        > lowering the price will **not** solve customer dissatisfaction. Retailers should investigate the supplier first.
        """)

    # AI Raw Output (if available)
    if review_data.get("ai_powered") and review_data.get("ai_raw_output"):
        with st.expander("🤖 View Full NVIDIA NIM LLM Analysis Response"):
            st.markdown(review_data["ai_raw_output"])

    # Raw Customer Reviews Table
    st.markdown("---")
    st.subheader(f"💬 Raw Customer Reviews for {p_info['product_name']}")
    p_revs = reviews_df[reviews_df["product_id"] == selected_pid]
    if not p_revs.empty:
        st.dataframe(
            p_revs[["review_id", "review_date", "rating", "review_text"]].sort_values("rating"),
            use_container_width=True
        )
    else:
        st.write("No reviews logged for this product.")


# =============================================================
# MODULE 3: SMART PRICING & DISCOUNT SIMULATOR
# =============================================================
elif page == "🏷️ 3. Smart Pricing & Discount":
    st.title("🏷️ Smart Pricing & Discount Simulator")
    st.markdown("Deterministic financial metrics, target margin feasibility, market price benchmarking, and interactive discount scenario modeling.")

    # Product Selector
    selected_pid = render_product_selector("m3")
    p_info = products_df[products_df["product_id"] == selected_pid].iloc[0]

    # Calculate Pricing Metrics
    p_metrics = calculate_price_metrics(p_info, competitors_df)

    # Section A: Current Financial Metrics
    st.subheader("💵 Financial & Unit Margin Breakdown")
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
    
    with m_col1:
        st.metric(
            "Total Unit Cost",
            f"₹{p_metrics['unit_cost']:,.2f}",
            f"Base: ₹{p_info['purchase_cost']:,.0f} + Var: ₹{p_info['variable_cost']:,.0f}"
        )
    with m_col2:
        st.metric(
            "Current Selling Price",
            f"₹{p_metrics['selling_price']:,.2f}"
        )
    with m_col3:
        st.metric(
            "Unit Gross Profit",
            f"₹{p_metrics['unit_profit']:,.2f}",
            f"Markup: {p_metrics['markup_percent']:.1f}%"
        )
    with m_col4:
        margin_status = "✅ Met" if p_metrics["target_margin_achieved"] else "❌ Under"
        st.metric(
            "Current Gross Margin",
            f"{p_metrics['margin_percent']:.1f}%",
            f"Target: {p_metrics['target_margin_percent']:.1f}% ({margin_status})"
        )
    with m_col5:
        st.metric(
            "Min Price for Target",
            f"₹{p_metrics['minimum_price_for_target']:,.2f}",
            f"Formula: Cost / (1 - Target)"
        )

    # Competitor Benchmark Callout
    if p_metrics["competitor_median"]:
        delta = p_metrics["competitor_diff"]
        delta_str = f"+₹{delta:,.2f}" if delta > 0 else f"-₹{abs(delta):,.2f}"
        st.markdown(
            f"**Competitor Benchmark:** Median competitor price is **₹{p_metrics['competitor_median']:,.2f}** "
            f"({p_metrics['competitor_count']} market sources observed). "
            f"Your price is **{delta_str}** relative to the competitor median."
        )

    if not p_metrics["target_margin_achieved"]:
        st.error(p_metrics["pricing_action"])
    else:
        st.success(p_metrics["pricing_action"])

    st.markdown("---")

    # Section B: Interactive Discount Simulator
    st.subheader("🎛️ Interactive Discount Simulator")
    st.markdown("Test proposed discount percentages to immediately view the impact on unit profit, gross margin, and required volume uplift.")

    disc_col1, disc_col2 = st.columns([4, 6])

    with disc_col1:
        discount_slider = st.slider(
            "Select Proposed Discount Percentage (%):",
            min_value=0.0,
            max_value=50.0,
            value=10.0,
            step=1.0,
            format="%.0f%%"
        )
        
        sim = simulate_discount(
            selling_price=p_metrics["selling_price"],
            unit_cost=p_metrics["unit_cost"],
            target_margin=p_info["target_margin"],
            discount_percent=discount_slider
        )
        
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {'#28a745' if sim['target_margin_maintained'] else '#dc3545'};">
            <div class="metric-title">Discounted Selling Price</div>
            <div class="metric-value">₹{sim['discounted_price']:,.2f}</div>
            <div class="metric-subtitle">Discount Amount: -₹{sim['discount_amount']:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"**Max Allowable Discount to Preserve Target Margin:** `{sim['max_allowable_discount_percent']:.1f}%`")

    with disc_col2:
        s1, s2, s3 = st.columns(3)
        with s1:
            st.metric("New Unit Profit", f"₹{sim['new_unit_profit']:,.2f}", f"Diff: ₹{sim['profit_difference_per_unit']:,.2f}")
        with s2:
            st.metric("New Gross Margin", f"{sim['new_margin_percent']:.1f}%", f"Target: {sim['target_margin_percent']:.1f}%")
        with s3:
            target_label = "✅ Maintained" if sim['target_margin_maintained'] else "❌ Breached"
            st.metric("Target Margin Status", target_label)
            
        st.markdown("#### ⚖️ Required Volume Uplift Analysis")
        if sim["uplift_feasible"]:
            st.info(f"📈 **Break-even Volume Requirement:** {sim['uplift_explanation']}")
        else:
            st.error(f"🚨 {sim['uplift_explanation']}")
            
        st.caption("Disclaimer: This is a pure mathematical break-even model, not an empirical prediction that sales demand will expand.")

    st.markdown("---")

    # Section C: Intelligent Heuristic Recommendation (Module 4)
    st.subheader("💡 Intelligent Business & Discount Recommendation")
    rec = recommend_discount(p_info, sales_df, reviews_df, competitors_df)

    # Style recommendation card based on urgency
    box_class = (
        "rec-box-danger" if rec["urgency"] == "High"
        else ("rec-box-warning" if rec["urgency"] == "Moderate" else "rec-box-success")
    )
    
    st.markdown(f"""
    <div class="{box_class}">
        <h4 style="margin: 0 0 8px 0;">🎯 Recommended Strategy: {rec['action_type']}</h4>
        <p style="margin: 0; font-size: 0.95rem;">
            <strong>Urgency:</strong> {rec['urgency']} &nbsp;|&nbsp; 
            <strong>Suggested Discount Window:</strong> {rec['suggested_discount_range']} &nbsp;|&nbsp; 
            <strong>Sales Velocity:</strong> {rec['sales_trend_direction']} ({rec['sales_velocity_status']})
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🔍 Explainable Business Rationale:")
    for reason in rec["reasons"]:
        st.markdown(f"- {reason}")


# =============================================================
# MODULE 4: AI RETAIL ADVISOR
# =============================================================
elif page == "🤖 4. AI Retail Advisor":
    st.title("🤖 AI Retail Advisor & Business Assistant")
    st.markdown("Ask natural-language business questions grounded strictly in deterministic calculations and actual customer reviews.")

    # Product Selector
    selected_pid = render_product_selector("m4")
    
    # Compile complete grounded context
    product_context = compile_product_context(
        selected_pid, products_df, sales_df, reviews_df, competitors_df
    )
    
    # Grounded Fact Snapshot Card
    with st.expander("📋 View Grounded Product Facts Injected into AI (Python Source of Truth)", expanded=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            st.markdown(f"**Selling Price:** ₹{product_context['selling_price']:,.2f}")
            st.markdown(f"**Total Unit Cost:** ₹{product_context['unit_cost']:,.2f}")
        with f_col2:
            st.markdown(f"**Gross Margin:** {product_context['margin_percent']:.1f}%")
            st.markdown(f"**Target Margin:** {product_context['target_margin_percent']:.1f}%")
        with f_col3:
            st.markdown(f"**Stock Level:** {product_context['stock']} units")
            st.markdown(f"**Inventory Age:** {product_context['inventory_age_days']} days")
        with f_col4:
            st.markdown(f"**Rating:** {product_context['average_rating']:.1f}/5.0 ({product_context['total_reviews']} revs)")
            st.markdown(f"**Rule Action:** {product_context['action_type']}")

    st.markdown("---")
    st.subheader("💬 Ask RetailPulse Advisor")

    # Quick Question Buttons
    st.markdown("**Quick Inquiries:**")
    q_col1, q_col2, q_col3 = st.columns(3)
    preset_query = None
    
    with q_col1:
        if st.button("📉 Why are sales declining?", use_container_width=True):
            preset_query = "Why are sales of this product declining and what is the root cause?"
    with q_col2:
        if st.button("🏷️ Should I give a discount?", use_container_width=True):
            preset_query = "Should I offer a discount on this product, and what are the margin implications?"
    with q_col3:
        if st.button("⚠️ What are customers complaining about?", use_container_width=True):
            preset_query = "What are customers appreciating or complaining about in product reviews?"

    # Custom Query Input
    user_query = st.text_input(
        "Or type your custom question here:",
        value=preset_query if preset_query else "",
        placeholder="e.g., Explain why you recommend investigating complaints before discounting this item."
    )

    if st.button("Get AI Retail Advisory", type="primary") or preset_query:
        query_to_run = user_query if user_query else preset_query
        if query_to_run:
            with st.spinner("Analyzing facts and generating retail advice..."):
                resp = ask_retail_advisor(query_to_run, product_context)
                
            st.markdown(f"### 💡 Advisor Response")
            st.caption(f"Inference Source: {resp['source']}")
            st.markdown(resp["answer"])
            
            st.markdown("""
            ---
            <small style="color: #6c757d;">
            <strong>Architectural Assurance:</strong> RetailPulse AI strictly grounds AI responses in Python-verified 
            financial calculations and actual CSV customer reviews. The AI model does not hallucinate figures.
            </small>
            """, unsafe_allow_html=True)
        else:
            st.warning("Please type a question or select a quick inquiry above.")
