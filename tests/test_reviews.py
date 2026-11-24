"""
test_reviews.py - Unit Tests for Review Analysis & Fallback Engine
Part of RetailPulse AI Test Suite
"""

import pytest
import pandas as pd
from review_engine import analyze_reviews, extract_local_review_insights
from nvidia_client import ask_nvidia, get_nvidia_config


def test_review_analysis_offline_fallback():
    """Verify that review analysis works seamlessly without NVIDIA API key."""
    reviews_df = pd.DataFrame([
        {"product_id": "PRD002", "rating": 2, "review_text": "Battery life is terrible, dies in 2 hours."},
        {"product_id": "PRD002", "rating": 1, "review_text": "Left earbud battery drains immediately."},
        {"product_id": "PRD002", "rating": 4, "review_text": "Sound is good with nice bass."}
    ])
    result = analyze_reviews("PRD002", reviews_df, use_ai=False)
    assert result["average_rating"] == 2.33
    assert result["total_reviews"] == 3
    assert "Battery Life & Drainage" in result["common_complaints"]
    assert len(result["positive_themes"]) > 0
    assert len(result["negative_themes"]) > 0
    assert len(result["suggested_actions"]) > 0


def test_review_analysis_empty_reviews():
    """Verify empty reviews handling without exceptions."""
    empty_df = pd.DataFrame()
    result = analyze_reviews("PRD999", empty_df, use_ai=False)
    assert result["total_reviews"] == 0
    assert result["average_rating"] == 0.0
    assert "No customer feedback" in result["summary"]


def test_nvidia_missing_key_graceful_handling():
    """Verify that ask_nvidia returns fallback flag when unconfigured without raising exceptions."""
    resp = ask_nvidia("Test prompt")
    assert resp["success"] is False
    assert resp["fallback_used"] is True
    assert "NVIDIA_API_KEY" in resp["error"]
