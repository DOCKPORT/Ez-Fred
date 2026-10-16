"""Series configuration for Ez-Fred.

Master source of truth. Each category group writes its own JSON file in the Data folder.
The group key is the file name without the extension. For example "inflation" writes inflation.json.
"""

FRED_SERIES_CONFIG = {
    "monetary": {
        "name": "Monetary Policy",
        "series": {
            "DFEDTARU": {"name": "Fed Funds Upper Target", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
            "EFFR": {"name": "Effective Federal Funds Rate", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
            "DFEDTARL": {"name": "Fed Funds Lower Target", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
        },
    },
    "inflation": {
        "name": "Inflation",
        "series": {
            "CPIAUCSL": {"name": "Consumer Price Index", "yoy_type": "pc1", "prefix": "", "suffix": ""},
            "PPIFIS": {"name": "Producer Price Index", "yoy_type": "pc1", "prefix": "", "suffix": ""},
            "PCEPILFE": {"name": "Core PCE Price Index", "yoy_type": "pc1", "prefix": "", "suffix": ""},
            "CPILFESL": {"name": "Core CPI", "yoy_type": "pc1", "prefix": "", "suffix": ""},
            "PCEPI": {"name": "PCE Price Index", "yoy_type": "pc1", "prefix": "", "suffix": ""},
        },
    },
    "ustreasuries": {
        "name": "US Treasury Yields",
        "series": {
            "DGS1MO": {"name": "US 1-Month Bond Yield", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
            "DGS3MO": {"name": "US 3-Month Bond Yield", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
            "DGS6MO": {"name": "US 6-Month Bond Yield", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
            "DGS1": {"name": "US 1-Year Bond Yield", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
            "DGS2": {"name": "US 2-Year Bond Yield", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
            "DGS3": {"name": "US 3-Year Bond Yield", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
            "DGS5": {"name": "US 5-Year Bond Yield", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
            "DGS7": {"name": "US 7-Year Bond Yield", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
            "DGS10": {"name": "US 10-Year Bond Yield", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
            "DGS20": {"name": "US 20-Year Bond Yield", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
            "DGS30": {"name": "US 30-Year Bond Yield", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
        },
    },
    "sentiment": {
        "name": "Sentiment",
        "series": {
            "VIXCLS": {"name": "CBOE Volatility Index (VIX)", "yoy_type": "pc1", "prefix": "", "suffix": ""},
            "STLFSI4": {"name": "Fed Financial Stress Index", "yoy_type": "ch1", "prefix": "", "suffix": ""},
            "UMCSENT": {"name": "Consumer Sentiment Index", "yoy_type": "pc1", "prefix": "", "suffix": ""},
        },
    },
    "labor": {
        "name": "Labor Market",
        "series": {
            "UNRATE": {"name": "Unemployment Rate", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
            "PAYEMS": {"name": "Nonfarm Payrolls", "yoy_type": "pc1", "prefix": "", "suffix": ""},
            "ICSA": {"name": "Initial Jobless Claims", "yoy_type": "pc1", "prefix": "", "suffix": ""},
            "CCSA": {"name": "Continuing Jobless Claims", "yoy_type": "pc1", "prefix": "", "suffix": ""},
            "JTSJOL": {"name": "Job Openings (JOLTS)", "yoy_type": "pc1", "prefix": "", "suffix": ""},
            "CIVPART": {"name": "Labor Force Participation Rate", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
            "U6RATE": {"name": "U-6 Unemployment Rate", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
        },
    },
    "commodities": {
        "name": "Commodities",
        "series": {
            "DCOILBRENTEU": {"name": "Brent Crude Oil", "yoy_type": "pc1", "prefix": "$", "suffix": ""},
            "DCOILWTICO": {"name": "WTI Crude Oil", "yoy_type": "pc1", "prefix": "$", "suffix": ""},
            "GASREGW": {"name": "US Gasoline Price", "yoy_type": "pc1", "prefix": "$", "suffix": ""},
            "PCOPPUSDM": {"name": "Copper Global Price", "yoy_type": "pc1", "prefix": "$", "suffix": ""},
            "PALUMUSDM": {"name": "Aluminum Global Price", "yoy_type": "pc1", "prefix": "$", "suffix": ""},
            "PZINCUSDM": {"name": "Zinc Global Price", "yoy_type": "pc1", "prefix": "$", "suffix": ""},
            "PNICKUSDM": {"name": "Nickel Global Price", "yoy_type": "pc1", "prefix": "$", "suffix": ""},
        },
    },
    "equities": {
        "name": "Equity Indexes",
        "series": {
            "SP500": {"name": "S&P 500 Index", "yoy_type": "pc1", "prefix": "$", "suffix": ""},
            "NASDAQ100": {"name": "NASDAQ 100 Index", "yoy_type": "pc1", "prefix": "$", "suffix": ""},
            "DJIA": {"name": "Dow Jones Ind. Avg.", "yoy_type": "pc1", "prefix": "$", "suffix": ""},
            "NIKKEI225": {"name": "Nikkei 225", "yoy_type": "pc1", "prefix": "JPY", "suffix": ""},
        },
    },
}
