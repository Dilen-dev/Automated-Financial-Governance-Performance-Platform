CREATE TABLE IF NOT EXISTS public.dim_asset_master (
    trading_symbol VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(255),
    created_at_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pipeline_run_id VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS public.fact_market_performance (
    trading_symbol VARCHAR(50) REFERENCES public.dim_asset_master(trading_symbol),
    trading_date DATE,
    open_price NUMERIC(12,4),
    high_price NUMERIC(12,4),
    low_price NUMERIC(12,4),
    close_price NUMERIC(12,4),
    volume NUMERIC(18,4),
    created_at_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pipeline_run_id VARCHAR(100),
    PRIMARY KEY (trading_symbol, trading_date)
);

CREATE TABLE IF NOT EXISTS public.fact_governance_audit (
    trading_symbol VARCHAR(50) REFERENCES public.dim_asset_master(trading_symbol),
    audit_date DATE,
    internal_score NUMERIC(5,2),
    environmental_score NUMERIC(5,2),
    social_score NUMERIC(5,2),
    governance_score NUMERIC(5,2),
    operational_risk_tier VARCHAR(50),
    created_at_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pipeline_run_id VARCHAR(100),
    PRIMARY KEY (trading_symbol, audit_date)
);

-- Optimization Indexes
CREATE INDEX IF NOT EXISTS idx_market_perf_symbol_date ON public.fact_market_performance(trading_symbol, trading_date);
CREATE INDEX IF NOT EXISTS idx_gov_audit_symbol_date ON public.fact_governance_audit(trading_symbol, audit_date);
