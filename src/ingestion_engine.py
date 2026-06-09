import requests
import uuid
from datetime import datetime
import time
import pandas as pd
from sqlalchemy import text

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import API_BASE_URL, API_KEY, WATCH_LIST
from src.db_manager import get_engine, initialize_schema
from src.mock_governance import get_simulated_governance_audit

def fetch_asset_master() -> pd.DataFrame:
    print("Fetching Asset Master list...")
    url = f"{API_BASE_URL}/stock-symbols?key={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        df = pd.DataFrame(data)
        
        df = df[df['trading_symbol'].isin(WATCH_LIST)]
        if 'registrant_name' in df.columns:
            df.rename(columns={'registrant_name': 'company_name'}, inplace=True)
            
        df = df[['trading_symbol', 'company_name']]
        df = df[['trading_symbol', 'company_name']]
        
        # Inject missing ones due to pagination limits
        missing = set(WATCH_LIST) - set(df['trading_symbol'])
        if missing:
            fallback = pd.DataFrame([
                {'trading_symbol': 'AAPL', 'company_name': 'Apple Inc.'},
                {'trading_symbol': 'MSFT', 'company_name': 'MICROSOFT CORP'},
                {'trading_symbol': 'NVDA', 'company_name': 'NVIDIA Corp'},
                {'trading_symbol': 'GOOG', 'company_name': 'Alphabet Inc.'},
                {'trading_symbol': 'AMZN', 'company_name': 'Amazon.com, Inc.'}
            ])
            missing_df = fallback[fallback['trading_symbol'].isin(missing)]
            df = pd.concat([df, missing_df], ignore_index=True)
            
        return df
    except Exception as e:
        print(f"Warning: Failed to fetch stock-symbols data (mocking safely): {e}")
        return pd.DataFrame([
            {'trading_symbol': 'AAPL', 'company_name': 'Apple Inc.'},
            {'trading_symbol': 'MSFT', 'company_name': 'MICROSOFT CORP'},
            {'trading_symbol': 'NVDA', 'company_name': 'NVIDIA Corp'},
            {'trading_symbol': 'GOOG', 'company_name': 'Alphabet Inc.'},
            {'trading_symbol': 'AMZN', 'company_name': 'Amazon.com, Inc.'}
        ])

def fetch_market_performance(symbol: str) -> pd.DataFrame:
    print(f"Fetching market performance for {symbol}...")
    url = f"{API_BASE_URL}/stock-prices?identifier={symbol}&key={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        df = pd.DataFrame(data)
        
        df.rename(columns={
            'date': 'trading_date',
            'open': 'open_price',
            'high': 'high_price',
            'low': 'low_price',
            'close': 'close_price'
        }, inplace=True)
        return df
    except Exception as e:
        print(f"Warning: Failed to fetch market data for {symbol}: {e}")
        return pd.DataFrame()

def run_pipeline():
    run_id = str(uuid.uuid4())
    print(f"Starting Ingestion Pipeline Run: {run_id}")
    
    initialize_schema()
    engine = get_engine()
    
    df_assets = fetch_asset_master()
    if not df_assets.empty:
        df_assets['pipeline_run_id'] = run_id
        try:
            with engine.begin() as conn:
                for _, row in df_assets.iterrows():
                    sql = """
                        INSERT INTO public.dim_asset_master (trading_symbol, company_name, pipeline_run_id) 
                        VALUES (:sym, :comp, :run)
                        ON CONFLICT (trading_symbol) DO UPDATE 
                        SET company_name = EXCLUDED.company_name, pipeline_run_id = EXCLUDED.pipeline_run_id;
                    """
                    conn.execute(text(sql), {"sym": row['trading_symbol'], "comp": row['company_name'], "run": run_id})
            print("Finished Asset Master UPSERT.")
        except Exception as e:
            print(f"Error during Asset Master UPSERT: {e}")

    today_str = datetime.today().strftime('%Y-%m-%d')
    for symbol in WATCH_LIST:
        time.sleep(2) # Prevent 429 Too Many Requests rate limits
        df_perf = fetch_market_performance(symbol)
        if not df_perf.empty:
            df_perf['pipeline_run_id'] = run_id
            try:
                with engine.begin() as conn:
                    for _, row in df_perf.iterrows():
                        sql = """
                            INSERT INTO public.fact_market_performance 
                            (trading_symbol, trading_date, open_price, high_price, low_price, close_price, volume, pipeline_run_id) 
                            VALUES (:sym, :td, :op, :hp, :lp, :cp, :vol, :run)
                            ON CONFLICT (trading_symbol, trading_date) DO UPDATE 
                            SET close_price = EXCLUDED.close_price, volume = EXCLUDED.volume, pipeline_run_id = EXCLUDED.pipeline_run_id;
                        """
                        conn.execute(text(sql), {
                            "sym": row['trading_symbol'], "td": row['trading_date'],
                            "op": row['open_price'], "hp": row['high_price'], 
                            "lp": row['low_price'], "cp": row['close_price'],
                            "vol": row['volume'], "run": run_id
                        })
                print(f"Loaded {len(df_perf)} rows of market performance for {symbol}")
            except Exception as e:
                print(f"Error during Market Performance UPSERT for {symbol}: {e}")

        # Simulate Governance data for today
        gov_audit = get_simulated_governance_audit(symbol, today_str)
        gov_audit['pipeline_run_id'] = run_id
        try:
            with engine.begin() as conn:
                sql = """
                    INSERT INTO public.fact_governance_audit
                    (trading_symbol, audit_date, internal_score, environmental_score, social_score, governance_score, operational_risk_tier, pipeline_run_id) 
                    VALUES (:sym, :dt, :ins, :env, :soc, :gov, :rt, :run)
                    ON CONFLICT (trading_symbol, audit_date) DO UPDATE 
                    SET internal_score = EXCLUDED.internal_score, 
                        operational_risk_tier = EXCLUDED.operational_risk_tier, 
                        pipeline_run_id = EXCLUDED.pipeline_run_id;
                """
                conn.execute(text(sql), {
                    "sym": gov_audit['trading_symbol'], "dt": gov_audit['audit_date'],
                    "ins": gov_audit['internal_score'], "env": gov_audit['environmental_score'],
                    "soc": gov_audit['social_score'], "gov": gov_audit['governance_score'],
                    "rt": gov_audit['operational_risk_tier'], "run": run_id
                })
        except Exception as e:
            print(f"Error during Governance UPSERT for {symbol}: {e}")

    print("Pipeline Execution Completed.")

if __name__ == "__main__":
    run_pipeline()
