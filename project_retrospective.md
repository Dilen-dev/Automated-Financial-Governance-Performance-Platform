# Project Retrospective: Automated Financial Governance Platform

This document outlines the technical hurdles encountered during the backend engineering and data engineering phases of the Automated Financial Governance & Performance Platform, and details the specific strategies implemented to resolve them.

## 1. Navigating Free-Tier API Pagination Limits
**Challenge:** We needed to initialize our PostgreSQL `dim_asset_master` table using the `stock-symbols` API endpoint to establish a unified list of active corporate assets. However, the Free Tier of the FinancialData.net API restricts payloads to the first 500 records. As a result, assets like `AAPL` and `AMZN` were fetched successfully, but `MSFT`, `NVDA`, and `GOOG` were paginated out.

**Symptom:** When the pipeline progressed to extract daily market performance for the missing assets, PostgreSQL's strict relational integrity intervened. The database threw `psycopg2.errors.ForeignKeyViolation` exceptions, correctly blocking the orphan records from being inserted into the `fact_market_performance` table because they didn't exist in the Dimension table.

**Resolution:** Instead of writing complex pagination loops that would rapidly burn through the Free Tier daily limit (300 requests/day), we utilized Python's `pandas` library to perform a set-difference check during ingestion. Any mandated symbol missing from the API payload was programmatically injected into the DataFrame before UPSERTing into PostgreSQL, entirely bypassing the pagination limit while preserving rigorous database integrity constraints.

## 2. Circumventing strict API Rate Limits (HTTP 429)
**Challenge:** To calculate the 30-day volatility views, we loop through our watchlist to fetch historical data for each asset. The initial execution failed midway through the loop, returning `HTTP 429: Too Many Requests` errors from the server.

**Resolution:** This is standard API throttling. We quickly re-engineered the Python ingestion pipeline, importing the `time` module and introducing a `time.sleep(2)` buffer inside the iteration loop. This effectively decoupled the immediate execution of requests, allowing the script to safely crawl the data across the Free Tier endpoints completely undetected by standard rate mitigations.

## 3. Resolving Internal Network Hostname Constraints
**Challenge:** The user initially provided the database address as `myserver`, which corresponded to their internal naming convention within pgAdmin. When the `psycopg2` driver attempted to connect, the system network layer raised a `No such host is known` exception.

**Resolution:** Standardized PostgreSQL client groups do not automatically map to DNS namespaces. We intervened inside the root `.env` configuration file, redirecting the `DB_HOST` variable from `myserver` to the standardized `localhost` loopback address, immediately restoring downstream connectivity.

## 4. API Authentication Payload Structures
**Challenge:** Most standard financial APIs expect authentication tokens via HTTP Headers (e.g., `Authorization: Bearer <token>`). An initial test probe yielded a `401 Unauthorized` drop.

**Resolution:** By reviewing the FinancialData.net documentation framework, we identified that the system relies exclusively on URL query strings. We retrofitted the `API_BASE_URL` logic across the entire ingestion engine to securely append the `?key=` parameter onto every single extraction request.

## 5. UI De-Synchronization
**Challenge:** The PostgreSQL database and architecture were created automatically by our initialization pipeline code. Upon visual inspection, the client IDE (pgAdmin) did not display the newly generated `financial_governance_db`.

**Resolution:** This is an expected artifact of managing databases programmatically out-of-band. The database state had mutated, but the UI had not naturally issued a `SELECT... FROM pg_database` refresh command. Simply triggering a manual UI-refresh resynced the client state to reveal the instantiated database, tables, and views smoothly.
