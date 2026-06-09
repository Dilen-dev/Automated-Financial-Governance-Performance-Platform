@echo off
echo =======================================================
echo Automated Financial Governance Pipeline
echo =======================================================

echo 1. Loading environment...
cd /d "%~dp0"
IF NOT EXIST ".env" (
    echo [ERROR] .env file not found. Ensure .env is placed in the project root.
    pause
    exit /b
)

echo 2. Installing/Updating requirements...
pip install -r requirements.txt

echo 3. Running Execution Engine...
set PYTHONPATH=%cd%
python src\ingestion_engine.py

echo.
echo =======================================================
echo Pipeline Completed successfully.
echo Please review the Power BI views in your DB client.
echo =======================================================
pause
