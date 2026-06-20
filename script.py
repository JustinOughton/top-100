.github/workflows/market_timer.yml
name: Option C Market Cloud Engine

on:
  schedule:
    # 1. Runs every hour on the hour, Monday to Friday, during US market hours (14:00 to 21:00 UTC)
    - cron: '0 14-21 * * 1-5'
    # 2. Runs once daily at 21:30 UTC (4:30 PM EST), right after the NYSE/NASDAQ market close
    - cron: '30 21 * * 1-5'
  workflow_dispatch: # Allows you to manually trigger the script from your phone anytime

jobs:
  run-market-engine:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout Repository Code
      uses: actions/checkout@v3

    - name: Set up Cloud Python Environment
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install Data Libraries
      run: pip install pandas yfinance numpy requests

    # If the trigger time is 21:30 UTC, execute the daily rebalance report
    - name: Run 24-Hour Market Close Rebalance
      if: github.event.schedule == '30 21 * * 1-5'
      run: python script.py --rebalance

    # If it is any other hour, run the standard ranking update loop
    - name: Run Hourly Matrix Update
      if: github.event.schedule != '30 21 * * 1-5'
      run: python script.py

    # Automatically save and push the updated CSV, HTML table, and TXT report back to your repository
    - name: Save and Commit Updated Outputs
      run: |
        git config --global user.name "Option-C-Cloud-Bot"
        git config --global user.email "bot@optionc.internal"
        git add active_100_tickers.csv current_ai_rankings.csv market_dashboard.html daily_market_close_report.txt
        git commit -m "Automated Sync: Cloud data layer metrics refreshed" || exit 0
        git push
