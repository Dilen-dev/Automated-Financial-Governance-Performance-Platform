import os
import random

def get_simulated_governance_audit(symbol, audit_date):
    """
    Programmatically generates an ESG/Internal Corporate Governance rating.
    A score of 1-100 where >80 is excellent, and <50 is a governance risk.
    """
    # Create variance so some stocks will trigger the GRC Exception rule (< 50)
    base_scores = {
        "AAPL": 85.0,
        "MSFT": 88.0,
        "NVDA": 48.0, # Purposely borderline to occasionally cross exception rule
        "GOOG": 80.0,
        "AMZN": 45.0  # Start lower to simulate risk
    }
    
    base = base_scores.get(symbol, 75.0)
    variation = random.uniform(-4.0, 4.0)
    score = round(max(0, min(100, base + variation)), 2)
    
    if score >= 80:
        tier = "Tier 1 - Optimal"
    elif score >= 50:
        tier = "Tier 2 - Monitor"
    else:
        tier = "Tier 3 - Critical"
        
    return {
        "trading_symbol": symbol,
        "audit_date": audit_date,
        "internal_score": score,
        "environmental_score": round(min(100, score + random.uniform(0, 5)), 2),
        "social_score": round(min(100, score + random.uniform(0, 5)), 2),
        "governance_score": score,
        "operational_risk_tier": tier
    }
