# Product Requirements Document (PRD)
## Project Name: RetailPulse AI
**Subtitle:** Intelligent Retail Pricing, Discount & Customer Satisfaction Intelligence System  
**Target Users:** Retail shop owners, store managers, and category merchandisers  
**Team:** 4 B.Tech CSE (AI & ML) Students  
**Document Version:** 1.0.0  
**Status:** Approved for Implementation  

---

## 1. Executive Summary
Small and medium retailers frequently make suboptimal pricing and discounting decisions because they lack integrated intelligence connecting customer satisfaction, cost structures, and sales velocity. Typical mistakes include offering blanket discounts on products suffering from quality defects rather than price resistance, or slashing prices on fast-moving items with depleted stock.

**RetailPulse AI** is a decision-support platform designed specifically for retailers. It combines deterministic Python-based financial models with NVIDIA NIM LLM capabilities to deliver actionable intelligence on pricing, promotions, and customer review sentiment.

---

## 2. Business Objectives
RetailPulse AI addresses the 7 key retail questions:
1. **Customer Satisfaction:** Are customers satisfied with the products being sold?
2. **Review Insights:** What specific attributes are customers appreciating or complaining about?
3. **Price Soundness:** Is the current selling price appropriate relative to unit cost, margin, and competitors?
4. **Target Margin Realization:** What selling price is required to attain the retailer's target gross margin?
5. **Discount Strategy:** Should the retailer offer a discount, maintain price, or avoid discounting?
6. **Promotion Feasibility:** When is a promotional discount economically viable and volume-justifiable?
7. **Actionable Operations:** What concrete operational steps (supplier audit, repackaging, clearance) should be taken?

---

## 3. Product Scope & Functional Modules

### Module 1: Retail Overview Dashboard
- **Executive KPIs:** Total Revenue (₹), Total Gross Profit (₹), Total Units Sold, Average Product Rating, Total Inventory Units.
- **Visual Analytics:**
  - Sales Trend Over Time (Interactive Plotly line chart).
  - Product-wise Revenue & Units Sold comparison (Bar chart).
  - Gross Margin comparison across catalog.
  - Stock level vs. Reorder threshold visualization.
  - Best-performing vs. Slow-moving product matrix.
- **Rule:** 100% computed via Pandas/NumPy from sales and inventory data. No hallucinations.

### Module 2: Product Satisfaction Intelligence
- **Product Selector:** Interactive dropdown to inspect individual SKUs.
- **Satisfaction Metrics:** SKU-level average rating, total review count, rating distribution.
- **Qualitative Extraction (NVIDIA NIM / Fallback):**
  - Top positive feedback themes.
  - Top negative feedback themes and customer pain points.
  - Customer satisfaction executive summary.
  - Recommended retailer actions (e.g., supplier inquiry, QA inspection).
- **Graceful Fallback:** If NVIDIA NIM API is unavailable or unconfigured, an offline frequency and sentiment heuristic extracts top themes without crashing.

### Module 3: Smart Pricing & Discount Engine
- **Financial Metric Breakdown:**
  - Unit Cost = Purchase Cost + Variable Cost.
  - Unit Profit = Current Selling Price - Unit Cost.
  - Gross Profit Margin (%) = (Unit Profit / Selling Price) * 100.
  - Markup (%) = (Unit Profit / Unit Cost) * 100.
  - Minimum Selling Price for Target Margin = Unit Cost / (1 - Target Margin Decimal).
  - Competitor median price comparison.
- **Interactive Discount Simulator:**
  - Slider: 0% to 50% discount (step size: 1%).
  - Dynamic Outputs: Discounted price, discount amount, new unit profit, new gross margin, profit difference per unit.
  - Target Margin Viability Check: Boolean status indicator.
  - Maximum allowable discount that preserves target margin.
  - Required Sales Volume Uplift: `((Current Unit Profit / Discounted Unit Profit) - 1) * 100`. Guarded against division-by-zero or negative profit cases.

### Module 4: Intelligent Discount Recommendation
- **Multi-Factor Decision Matrix:** Evaluates 30-day sales velocity, inventory stock & age, customer rating & review sentiment, profit margin cushion, and competitor benchmark.
- **Recommendation Classifications:**
  1. *Maintain current price* (Balanced demand, adequate margin).
  2. *Avoid unnecessary discount* (High velocity, low stock; discounting burns margin unnecessarily).
  3. *Consider a small controlled promotion* (Declining velocity, excess stock, healthy margin cushion).
  4. *Investigate product quality or customer complaints first* (Sub-par rating, negative review trends; price cuts do not fix broken products).
  5. *Consider a phased markdown for slow-moving or old inventory* (Aged stock > 60 days, low velocity; liquidity preservation).
  6. *Review competitor positioning* (Selling price significantly above competitor median without quality differentiation).
- **Explainability:** Clear bulleted reasons explaining the business logic behind each recommendation.

### Module 5: NVIDIA AI Retail Advisor
- Natural-language interactive advisor grounded strictly in calculated metrics.
- Accepts natural language queries (e.g., "Why are sales of Wireless Headphones dropping?", "Should I discount the Smartwatch?").
- System prompt injects computed metrics (cost, margin, stock, rating, competitor benchmark) so the LLM acts as an analytical business consultant, never inventing numbers.

---

## 4. Technical Non-Functional Requirements
- **Technology Stack:** Python 3.10+, Streamlit, Pandas, NumPy, Plotly Express/Graph Objects, OpenAI Python SDK (configured for NVIDIA NIM), python-dotenv, pytest.
- **Reliability:** Zero-crash architecture. System functions 100% offline using deterministic fallbacks if NVIDIA API keys are absent or network requests time out.
- **Data Integrity:** Strict mathematical validation: no division by zero, non-negative prices, bounds checking on margins.
- **Localisation:** All currency values explicitly formatted in Indian Rupees (₹).
- **Demonstration Ready:** Pre-loaded with 5 distinct business scenarios highlighting real retail problems.
