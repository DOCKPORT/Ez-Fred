<p align="center">
  <img src="logo/FRED_Logo_Home_Page_a.svg" alt="ez-fred">
</p>

`Repo in early development`

# Ez-Fred

Free, no-limit and keyless API for most common FRED (Federal Reserve Economic Data) endpoints.

## What this repo solves

To use FRED API directly, you would have to create an account and request an API key. And you would have to deal with their strict limits. You would have to spend time scripting safe connections, and dealing with an API key.

This repo fetches and stores all the data daily, and is easily accessible as a JSON via raw.githubusercontent.com

## Endpoints

One JSON file per category, served via raw.githubusercontent.com:

- https://raw.githubusercontent.com/DOCKPORT/Ez-Fred/main/Data/monetary.json
- https://raw.githubusercontent.com/DOCKPORT/Ez-Fred/main/Data/inflation.json
- https://raw.githubusercontent.com/DOCKPORT/Ez-Fred/main/Data/ustreasuries.json
- https://raw.githubusercontent.com/DOCKPORT/Ez-Fred/main/Data/sentiment.json
- https://raw.githubusercontent.com/DOCKPORT/Ez-Fred/main/Data/commodities.json
- https://raw.githubusercontent.com/DOCKPORT/Ez-Fred/main/Data/equities.json

## Data Series

The repo fetches 27 series from FRED, split into one JSON file per category. Each entry stores the latest value and the value from one year ago.

### Monetary Policy (monetary.json)
- DFEDTARU — Fed Funds Upper Target
- FEDFUNDS — Fed Funds Effective Rate
- DFEDTARL — Fed Funds Lower Target

### Inflation (inflation.json)
- CPIAUCSL — Consumer Price Index
- PPIFIS — Producer Price Index
- PCEPILFE — Core PCE Price Index

### US Treasury Yields (ustreasuries.json)
- DGS1MO — US 1-Month Bond Yield
- DGS3MO — US 3-Month Bond Yield
- DGS6MO — US 6-Month Bond Yield
- DGS1 — US 1-Year Bond Yield
- DGS2 — US 2-Year Bond Yield
- DGS3 — US 3-Year Bond Yield
- DGS5 — US 5-Year Bond Yield
- DGS7 — US 7-Year Bond Yield
- DGS10 — US 10-Year Bond Yield
- DGS20 — US 20-Year Bond Yield
- DGS30 — US 30-Year Bond Yield

### Sentiment (sentiment.json)
- VIXCLS — CBOE Volatility Index (VIX)
- STLFSI4 — Fed Financial Stress Index
- UMCSENT — Consumer Sentiment Index

### Commodities (commodities.json)
- DCOILBRENTEU — Brent Crude Oil
- DCOILWTICO — WTI Crude Oil
- PCOPPUSDM — Copper Global Price
- PALUMUSDM — Aluminum Global Price

### Equity Indexes (equities.json)
- SP500 — S&P 500 Index
- NASDAQ100 — NASDAQ 100 Index
- DJIA — Dow Jones Ind. Avg.


## Data source
Source: https://fred.stlouisfed.org/

## Stack
- Python scripting
- GitHub Actions