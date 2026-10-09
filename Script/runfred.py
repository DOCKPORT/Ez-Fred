import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

# --- PATH RESOLUTION ---
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
DATA_DIR = os.path.join(project_root, "Data")
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Master source of truth. Each category group writes its own JSON file in the Data folder.
# The group key is the file name without the extension. For example "inflation" writes inflation.json.
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


def iter_series(config=None):
    """Yields (series_id, config) pairs across every category group."""
    groups = config or FRED_SERIES_CONFIG
    for group in groups.values():
        yield from group["series"].items()


def total_series(config=None):
    """Counts the configured series across every category group."""
    groups = config or FRED_SERIES_CONFIG
    return sum(len(group["series"]) for group in groups.values())


# Maps FRED unit codes to plain words for the JSON output.
CHANGE_TYPES = {
    "pc1": "percent",
    "ch1": "absolute",
}


class FredEconFetch:
    """
    High-performance FRED API data-fetching wrapper.
    Retrieves latest observation data with unit transformations.
    """
    FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
    REQUEST_TIMEOUT = (5, 10)
    YOY_WINDOW_DAYS = 550

    def __init__(self):
        self.session = requests.Session()
        # Adapt User-Agent to prevent bot-filtering
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Encoding": "gzip, deflate"
        })
        self.api_key = self._load_api_key()

    def _fetch(self, params, series_id):
        """Shared single GET request wrapper for FRED API endpoints."""
        try:
            response = self.session.get(self.FRED_BASE_URL, params=params, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code if http_err.response is not None else 0
            print(f"[!] Server error {status_code} for {series_id}: {http_err}")
            return None
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as conn_err:
            print(f"[!] Connection error for {series_id}: {conn_err}")
            return None
        except requests.exceptions.RequestException as e:
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

            year_ago_result = None
            change_result = None
            if prev_obs:
                try:
                    prev_val = float(prev_obs["value"])
                    year_ago_result = {
                        "date": prev_obs["date"],
                        "value": prev_val
                    }
                    if prev_val != 0:
                        if yoy_type == "pc1":
                            val = ((latest_val - prev_val) / prev_val) * 100.0
                        else: # "ch1"
                            val = latest_val - prev_val

                        change_result = {
                            "type": CHANGE_TYPES.get(yoy_type, "absolute"),
                            "value": round(val, 4)
                        }
                except Exception:  # noqa: BLE001, S110
                    pass

            return {
                "latest": {"date": latest_date_str, "value": latest_val},
                "YoY": year_ago_result,
                "change": change_result
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

        for sid, cfg in iter_series(config):
            # Sleep 0.5 seconds between sequential requests to prevent FRED rate limiting
            time.sleep(0.5)
            yoy_type = cfg.get("yoy_type", "pc1")
            res = self.get_observation_with_yoy(sid, yoy_type)
            if res:
                results[sid] = res

        return results


def build_group_output(category_name, group, results):
    """Builds the JSON payload for one category group."""
    series = {}
    for sid, cfg in group["series"].items():
        res = results.get(sid)
        if not res:
            continue
        series[sid] = {
            "name": cfg["name"],
            "display": {"prefix": cfg["prefix"], "suffix": cfg["suffix"]},
            "latest": res.get("latest"),
            "YoY": res.get("YoY"),
            "change": res.get("change"),
        }
    return {
        "meta": {
            "category": category_name,
            "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "series_count": len(series),
        },
        "series": series,
    }


def write_json(payload, path):
    """Writes the payload to a file as pretty JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def write_group_files(results, config=None):
    """Writes one JSON file per category group. Returns the written paths."""
    groups = config or FRED_SERIES_CONFIG
    written = []
    for group_key, group in groups.items():
        path = os.path.join(DATA_DIR, f"{group_key}.json")
        write_json(build_group_output(group["name"], group, results), path)
        written.append(path)
    return written


if __name__ == "__main__":
    # Isolated CLI runner for local runs and GitHub Actions.
    print("======================================================================")
    print("                        EZ-FRED DATA FETCH RUN")
    print("======================================================================")

    fetcher = FredEconFetch()
    if not fetcher.api_key:
        print("[!] Critical: FRED API key missing. Set FRED_API_KEY or add Script/fred_key.py.")
        sys.exit(1)

    total = total_series()
    print(f"[*] Series configured : {total}")
    print("[*] Fetching data (sequential, ~0.5s delay each)...")

    start_time = time.time()
    results = fetcher.fetch_all()
    duration = time.time() - start_time

    print(f"[*] Duration          : {duration:.2f} seconds")
    print(f"[*] Series fetched     : {len(results)}/{total}")

    write_group_files(results)

    for group_key, group in FRED_SERIES_CONFIG.items():
        ok = sum(1 for sid in group["series"] if sid in results)
        missing = len(group["series"]) - ok
        flag = "" if missing == 0 else f"  ({missing} missing)"
        print(f"  [{ok}/{len(group['series'])}] {group['name']} -> {group_key}.json{flag}")

    print(f"[*] Files written to   : {DATA_DIR}")
    print("======================================================================")
