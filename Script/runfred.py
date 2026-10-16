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

from config import FRED_SERIES_CONFIG  # noqa: E402


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
    MAX_ATTEMPTS = 4
    RETRY_BASE_DELAY = 2.0
    RETRYABLE_STATUS = (429, 500, 502, 503, 504)

    def __init__(self):
        self.session = requests.Session()
        # Adapt User-Agent to prevent bot-filtering
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Encoding": "gzip, deflate"
        })
        self.api_key = self._load_api_key()

    def _fetch(self, params, series_id):
        """
        Shared GET request wrapper for FRED API endpoints.
        Retries transient failures (connection errors, timeouts, HTTP 429 and 5xx).
        A permanent failure (HTTP 4xx other than 429) returns None at once.
        """
        delay = self.RETRY_BASE_DELAY
        last_error = ""

        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                response = self.session.get(self.FRED_BASE_URL, params=params, timeout=self.REQUEST_TIMEOUT)
                if response.status_code in self.RETRYABLE_STATUS:
                    raise requests.exceptions.HTTPError(
                        f"retryable status {response.status_code}", response=response
                    )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as http_err:
                status_code = http_err.response.status_code if http_err.response is not None else 0
                if status_code not in self.RETRYABLE_STATUS:
                    print(f"[!] Server error {status_code} for {series_id}: {http_err}")
                    return None
                last_error = f"Server error {status_code}"
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as conn_err:
                last_error = f"Connection error: {conn_err}"
            except ValueError as json_err:
                # A malformed body can be transient. Retry it.
                last_error = f"JSON decode error: {json_err}"
            except requests.exceptions.RequestException as e:
                print(f"[!] Request error for {series_id}: {e}")
                return None

            if attempt < self.MAX_ATTEMPTS:
                print(f"[!] Attempt {attempt}/{self.MAX_ATTEMPTS} failed for {series_id} ({last_error}). Retry in {delay:.0f}s.")
                time.sleep(delay)
                delay *= 2

        print(f"[!] All {self.MAX_ATTEMPTS} attempts failed for {series_id}: {last_error}")
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

        today = datetime.now(timezone.utc)  # noqa: UP017
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

            latest_dt = datetime.strptime(latest_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)  # noqa: UP017

            # Scan for the observation closest to 1 year ago (handles monthly/daily series)
            prev_obs = None
            min_diff = float('inf')
            for obs in valid_obs:
                obs_dt = datetime.strptime(obs["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)  # noqa: UP017
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


def load_existing_series(path):
    """
    Reads the previous JSON file and returns its series map.
    Returns an empty map when the file is absent or unreadable.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as e:
        print(f"[!] Cannot read previous data at {path}: {e}")
        return {}
    series = payload.get("series")
    return series if isinstance(series, dict) else {}


def build_group_output(category_name, group, results, previous=None):
    """
    Builds the JSON payload for one category group.
    A series without fresh data keeps its previous entry. This rule prevents data loss.
    """
    previous = previous or {}
    series = {}
    stale = []

    for sid, cfg in group["series"].items():
        res = results.get(sid)
        if res:
            series[sid] = {
                "name": cfg["name"],
                "display": {"prefix": cfg["prefix"], "suffix": cfg["suffix"]},
                "latest": res.get("latest"),
                "YoY": res.get("YoY"),
                "change": res.get("change"),
            }
            continue
        old_entry = previous.get(sid)
        if old_entry:
            # Carry the last good value forward. Never write an empty series.
            series[sid] = old_entry
            stale.append(sid)

    return {
        "meta": {
            "category": category_name,
            "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),  # noqa: UP017
            "series_count": len(series),
            "stale_series": stale,
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
    """
    Writes one JSON file per category group.
    Returns a tuple: the written paths, and a map of group key to stale series IDs.
    """
    groups = config or FRED_SERIES_CONFIG
    written = []
    stale_map = {}
    for group_key, group in groups.items():
        path = os.path.join(DATA_DIR, f"{group_key}.json")
        payload = build_group_output(group["name"], group, results, load_existing_series(path))
        write_json(payload, path)
        stale_map[group_key] = payload["meta"]["stale_series"]
        written.append(path)
    return written, stale_map


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

    written, stale_map = write_group_files(results)

    for group_key, group in FRED_SERIES_CONFIG.items():
        fresh = sum(1 for sid in group["series"] if sid in results)
        stale = stale_map.get(group_key, [])
        unavailable = len(group["series"]) - fresh - len(stale)
        notes = []
        if stale:
            notes.append(f"{len(stale)} stale: {', '.join(stale)}")
        if unavailable:
            notes.append(f"{unavailable} unavailable")
        flag = f"  ({'; '.join(notes)})" if notes else ""
        print(f"  [{fresh}/{len(group['series'])}] {group['name']} -> {group_key}.json{flag}")

    print(f"[*] Files written to   : {DATA_DIR}")
    print("======================================================================")

    if len(results) < total:
        failed = total - len(results)
        print(f"[!] {failed} series returned no data after retries. Previous values were kept.")
        sys.exit(1)
