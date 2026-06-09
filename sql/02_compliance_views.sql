-- View for 30-day volatility using standard deviation
CREATE OR REPLACE VIEW public.vw_market_volatility AS
SELECT 
    trading_symbol,
    trading_date,
    close_price,
    STDDEV(close_price) OVER (
        PARTITION BY trading_symbol 
        ORDER BY trading_date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as stddev_30d,
    AVG(close_price) OVER (
        PARTITION BY trading_symbol 
        ORDER BY trading_date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as avg_30d
FROM public.fact_market_performance;

-- View for the GRC Exception Report blending market risk + governance risk
CREATE OR REPLACE VIEW public.vw_grc_exception_report AS
SELECT
    m.trading_symbol,
    a.company_name,
    m.trading_date,
    m.close_price,
    m.stddev_30d,
    m.avg_30d,
    CASE 
        WHEN m.avg_30d = 0 THEN 0 
        ELSE (m.stddev_30d / m.avg_30d) * 100 
    END as volatility_percentage,
    g.internal_score,
    g.operational_risk_tier,
    -- Compliance Rule: Volatility swing > 15% AND internal_score < 50
    CASE 
        WHEN (
            CASE WHEN m.avg_30d = 0 THEN 0 ELSE (m.stddev_30d / m.avg_30d) * 100 END > 15.0 
            AND g.internal_score < 50.0
        ) THEN 1 
        ELSE 0 
    END as is_compliance_violation
FROM public.vw_market_volatility m
JOIN public.dim_asset_master a ON m.trading_symbol = a.trading_symbol
LEFT JOIN public.fact_governance_audit g ON m.trading_symbol = g.trading_symbol AND m.trading_date = g.audit_date;
