import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

# --- PATH RESOLUTION ---
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
DATA_FILE = os.path.join(project_root, "Data", "data.json")
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Master Source of Truth containing configurations for all registered macro dashboard cards
FRED_SERIES_CONFIG = {
    # 1. Monetary Policy
    "DFEDTARU": {"name": "Fed Funds Upper Target", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
    "FEDFUNDS": {"name": "Fed Funds Effective Rate", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
    "DFEDTARL": {"name": "Fed Funds Lower Target", "yoy_type": "ch1", "prefix": "", "suffix": "%"},
    
    # 2. Inflation Indexes
    "CPIAUCSL": {"name": "Consumer Price Index", "yoy_type": "pc1", "prefix": "", "suffix": ""},
    "PPIFIS": {"name": "Producer Price Index", "yoy_type": "pc1", "prefix": "", "suffix": ""},
    "PCEPILFE": {"name": "Core PCE Price Index", "yoy_type": "pc1", "prefix": "", "suffix": ""},
    
    # 3. US Treasury Yields
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
    
    # 4. Sentiment
    "VIXCLS": {"name": "CBOE Volatility Index (VIX)", "yoy_type": "pc1", "prefix": "", "suffix": ""},
    "STLFSI4": {"name": "Fed Financial Stress Index", "yoy_type": "ch1", "prefix": "", "suffix": ""},
    "UMCSENT": {"name": "Consumer Sentiment Index", "yoy_type": "pc1", "prefix": "", "suffix": ""},
    
    # 5. Commodities
    "DCOILBRENTEU": {"name": "Brent Crude Oil", "yoy_type": "pc1", "prefix": "$", "suffix": ""},
    "DCOILWTICO": {"name": "WTI Crude Oil", "yoy_type": "pc1", "prefix": "$", "suffix": ""},
    "PCOPPUSDM": {"name": "Copper Global Price", "yoy_type": "pc1", "prefix": "$", "suffix": ""},
    "PALUMUSDM": {"name": "Aluminum Global Price", "yoy_type": "pc1", "prefix": "$", "suffix": ""},
    
    # 6. Equity Indexes
    "SP500": {"name": "S&P 500 Index", "yoy_type": "pc1", "prefix": "", "suffix": ""},
    "NASDAQ100": {"name": "NASDAQ 100 Index", "yoy_type": "pc1", "prefix": "", "suffix": ""},
    "DJIA": {"name": "Dow Jones Ind. Avg.", "yoy_type": "pc1", "prefix": "", "suffix": ""},
}

class FredEconFetch:
    """
    High-performance FRED API data-fetching wrapper.
    Retrieves latest observation data with unit transformations.
    """
    FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
    REQUEST_TIMEOUT = (5, 10)
    YOY_WINDOW_DAYS = 400

    # Error code constants
    ERROR_KEY_MISSING = "KEY_MISSING"
    ERROR_KEY_INVALID = "KEY_INVALID"
    ERROR_CONNECTION = "CONNECTION"
    ERROR_RATE_LIMIT = "RATE_LIMIT"
    ERROR_SERVER_ERROR = "SERVER_ERROR"

    def __init__(self):
        self.session = requests.Session()
        # Adapt User-Agent to prevent bot-filtering
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Encoding": "gzip, deflate"
        })
        self.api_key = self._load_api_key()
        self.last_error = None

    def _fetch(self, params, series_id):
        """Shared single GET request wrapper for FRED API endpoints."""
        try:
            response = self.session.get(self.FRED_BASE_URL, params=params, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code if http_err.response is not None else 0
            if status_code == 429:
                self.last_error = "FRED API Rate Limited (HTTP 429)"
            else:
                self.last_error = f"FRED Server Error (HTTP {status_code})"
            print(f"[!] Server error {status_code} for {series_id}: {http_err}")
            return None
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as conn_err:
            self.last_error = "FRED Connection/Timeout Error"
            print(f"[!] Connection error for {series_id}: {conn_err}")
            return None
        except requests.exceptions.RequestException as e:
            self.last_error = "FRED Request Exception"
            print(f"[!] Request error for {series_id}: {e}")
            return None

    def _load_api_key(self):
        """Loads the FRED API key from the environment or the local fred_key.py file."""
        env_key = os.environ.get("FRED_API_KEY", "").strip()
        if env_key:
            return env_key
        try:
            from fred_key import fred_api_key
            return str(fred_api_key).strip()
        except ImportError as e:  # noqa: BLE001, RUF100
            print(f"[!] Failed to load FRED API key: {e}")
            return ""

    def get_observation_with_yoy(self, series_id, yoy_type="pc1"):
        """
        Performs a single network request to fetch a rolling data window.
        Identifies the latest value and calculates the YoY transformation locally,
        eliminating a redundant round-trip API call.
        Supports: 'pc1' (Percent Change Year Ago) and 'ch1' (Absolute Change Year Ago).
        """
        if not self.api_key:
            return None

        today = datetime.now(timezone.utc)
        start_date = (today - timedelta(days=self.YOY_WINDOW_DAYS)).strftime("%Y-%m-%d")

        params = {
            "api_key": self.api_key,
            "series_id": series_id,
            "file_type": "json",
            "sort_order": "desc",
            "observation_start": start_date,
            "units": "lin"
        }

        data = self._fetch(params, series_id)
        if not data:
            return None

        try:
            observations = data.get("observations", [])
            if not observations:
                return None
            
            # Strip DOT placeholders and empty values
            valid_obs = [o for o in observations if o.get("value", "") not in ("", ".")]
            
            if not valid_obs:
                return None
            
            latest = valid_obs[0]
            latest_val_str = latest["value"]
            latest_date_str = latest["date"]
            
            try:
                latest_val = float(latest_val_str)
            except ValueError:
                return None
            
            latest_dt = datetime.strptime(latest_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            
            # Scan for the observation closest to 1 year ago (handles monthly/daily series)
            prev_obs = None
            min_diff = float('inf')
            for obs in valid_obs:
                obs_dt = datetime.strptime(obs["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                diff = abs((latest_dt - obs_dt).days - 365)
                if diff < min_diff:
                    min_diff = diff
                    prev_obs = obs
            
            yoy_result = None
            if prev_obs:
                try:
                    prev_val = float(prev_obs["value"])
                    if prev_val != 0:
                        if yoy_type == "pc1":
                            val = ((latest_val - prev_val) / prev_val) * 100.0
                        else: # "ch1"
                            val = latest_val - prev_val
                        
                        yoy_result = {
                            "date": latest_date_str,
                            "value": f"{val:.6f}"
                        }
                except Exception:  # noqa: BLE001, S110
                    pass
            
            return {
                "latest": {"date": latest_date_str, "value": latest_val_str},
                "yoy": yoy_result
            }
        except Exception as e:  # noqa: BLE001
            print(f"[!] Single-call YoY fetch error for {series_id}: {e}")
            return None

    def fetch_all(self, series_config=None):
        """
        Batch fetches multiple economic indicators sequentially.
        Sequential fetching prevents FRED API rate limits.
        """
        config = series_config or FRED_SERIES_CONFIG
        results = {}
        
        for sid, cfg in config.items():
            # Sleep 0.5 seconds between sequential requests to prevent FRED rate limiting
            time.sleep(0.5)
            yoy_type = cfg.get("yoy_type", "pc1")
            res = self.get_observation_with_yoy(sid, yoy_type)
            if res:
                results[sid] = res
                    
        return results

def build_output(results):
    """Builds the JSON payload that the data file stores."""
    return {
        "meta": {
            "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "https://fred.stlouisfed.org/",
            "series_count": len(results),
        },
        "series": {
            sid: {
                "name": FRED_SERIES_CONFIG[sid]["name"],
                "prefix": FRED_SERIES_CONFIG[sid]["prefix"],
                "suffix": FRED_SERIES_CONFIG[sid]["suffix"],
                "yoy_type": FRED_SERIES_CONFIG[sid]["yoy_type"],
                "latest": res.get("latest"),
                "yoy": res.get("yoy"),
            }
            for sid, res in results.items()
        },
    }


def write_json(payload, path=DATA_FILE):
    """Writes the payload to the data file as pretty JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


if __name__ == "__main__":
    # Isolated CLI runner for local runs and GitHub Actions.
    print("======================================================================")
    print("                        EZ-FRED DATA FETCH RUN")
    print("======================================================================")

    fetcher = FredEconFetch()
    if not fetcher.api_key:
        print("[!] Critical: FRED API key missing. Set FRED_API_KEY or add Script/fred_key.py.")
        sys.exit(1)

    print(f"[*] Series configured : {len(FRED_SERIES_CONFIG)}")
    print("[*] Fetching data (sequential, ~0.5s delay each)...")

    start_time = time.time()
    results = fetcher.fetch_all()
    duration = time.time() - start_time

    print(f"[*] Duration          : {duration:.2f} seconds")
    print(f"[*] Series fetched     : {len(results)}/{len(FRED_SERIES_CONFIG)}")

    write_json(build_output(results))

    for sid, conf in FRED_SERIES_CONFIG.items():
        status = "OK" if results.get(sid) else "MISSING"
        print(f"  [{status}] {conf['name']} ({sid})")

    print(f"[*] Data written to    : {DATA_FILE}")
    print("======================================================================")

