# Test Plan & Quality Assurance Specification
## Project Name: RetailPulse AI

---

## 1. Scope of Testing
Testing covers mathematical accuracy, edge-case resilience, heuristic recommendation correctness, offline fallback behavior, and UI stability.

---

## 2. Test Suite Breakdown

### 2.1 Pricing Engine Tests (`tests/test_pricing.py`)
- **TC-P01 (Normal Positive Profit):** Cost ₹1,000, Price ₹1,500. Expected Profit = ₹500, Margin = 33.33%, Markup = 50.0%.
- **TC-P02 (Zero Profit / At Cost):** Cost ₹1,000, Price ₹1,000. Expected Profit = ₹0, Margin = 0%, Markup = 0%.
- **TC-P03 (Loss / Below Cost):** Cost ₹1,000, Price ₹800. Expected Profit = -₹200, Margin = -25.0%, Markup = -20.0%.
- **TC-P04 (Target Margin Calculation):** Cost ₹1,000, Target Margin 20% (0.20). Expected Min Price = ₹1,250. Check verification: `(1250 - 1000)/1250 = 20%`.
- **TC-P05 (Target Margin Edge 0%):** Target margin 0% -> Min Price equals Cost.
- **TC-P06 (Target Margin Invalid >= 100%):** Handles invalid target margin >= 1.0 gracefully with ValueError or safe clamp.
- **TC-P07 (Competitor Benchmark):** Median calculation handles missing competitor rows or empty list gracefully.

### 2.2 Discount Engine Tests (`tests/test_discount.py`)
- **TC-D01 (Standard Simulation):** Cost ₹1,000, Price ₹1,500, 10% discount -> Discounted Price ₹1,350, Unit Profit ₹350, Margin 25.93%.
- **TC-D02 (Max Discount Maintaining Target Margin):** Cost ₹1,000, Price ₹1,500, Target Margin 20%. Max discount is calculated correctly without breaching target margin.
- **TC-D03 (Discount Resulting in Loss):** Cost ₹1,000, Price ₹1,200, 30% discount -> Discounted Price ₹840 (< Cost). Uplift is mathematically meaningless; function flags impossibility and returns safe warning.
- **TC-D04 (Volume Uplift Calculation):** Verify `((Current Profit / Discounted Profit) - 1) * 100` matches exact expected percentage.
- **TC-D05 (Heuristic Rules Validation):**
  - High sales velocity + low stock -> Suggests "Avoid unnecessary discount".
  - Declining sales + high stock + good rating -> Suggests "Consider a small controlled promotion".
  - Poor rating (< 3.5) with recurring complaints -> Suggests "Investigate product quality or customer complaints first".
  - Aged inventory (> 60 days) + low velocity -> Suggests "Consider a phased markdown".

### 2.3 Review & AI Fallback Tests
- **TC-R01 (Offline Fallback):** When `NVIDIA_API_KEY` is not present, `analyze_reviews()` generates valid positive themes, negative themes, and summary without raising an uncaught exception.
- **TC-R02 (Empty Reviews):** Product with zero reviews returns friendly "No customer reviews recorded yet" structure.

---

## 3. Test Execution Command
```bash
pytest -v tests/
```
All tests must pass with zero failures before deployment.
