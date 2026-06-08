name: Isabella's Alerts — Daily Briefing

on:
  schedule:
    - cron: '30 11 * * 1-5'   # 11:30 UTC = 7:30 AM ET (adjust to 30 12 in winter / EST)
  workflow_dispatch:            # allows manual trigger from GitHub UI

jobs:
  send-briefing:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install anthropic httpx

      - name: Send briefing
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          RESEND_API_KEY: ${{ secrets.RESEND_API_KEY }}
        run: python send_briefing.py
