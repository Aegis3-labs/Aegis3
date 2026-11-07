"""
Aegis3 Data Pipeline - Multi-Chain Explorer & RPC Scraper
Fetches transaction history, ERC-20 transfers, and contract call logs with caching and backoff.
Supports Etherscan, Arbiscan, Polygonscan, Optimism, and Base.
"""

import os
import time
import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any


# Standard API endpoints for major EVM networks
EXPLORER_APIS = {
    "ethereum": "https://api.etherscan.io/api",
    "arbitrum": "https://api.arbiscan.io/api",
    "polygon": "https://api.polygonscan.com/api",
    "optimism": "https://api-optimistic.etherscan.io/api",
    "base": "https://api.basescan.org/api",
}


class EtherscanClient:
    """
    Production-grade explorer client with local disk caching and adaptive rate limiting.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        chain: str = "ethereum",
        cache_dir: Optional[str] = None,
        requests_per_second: float = 4.0,
    ):
        self.api_key = api_key or os.environ.get("ETHERSCAN_API_KEY", "")
        self.chain = chain.lower().strip()
        self.base_url = EXPLORER_APIS.get(self.chain, EXPLORER_APIS["ethereum"])
        self.min_delay = 1.0 / requests_per_second
        self.last_request_time = 0.0

        # Setup local disk cache directory
        if cache_dir is None:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.cache_dir = os.path.join(root_dir, "cache", self.chain)
        else:
            self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, address: str, action: str) -> str:
        return os.path.join(self.cache_dir, f"{address.lower().strip()}_{action}.json")

    def _read_cache(self, address: str, action: str) -> Optional[List[Dict]]:
        cache_file = self._get_cache_path(address, action)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def _write_cache(self, address: str, action: str, data: List[Dict]):
        cache_file = self._get_cache_path(address, action)
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[EtherscanClient] Warning: Failed to write cache: {e}")

    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request_time = time.time()

    def _fetch_api(self, params: Dict[str, str], max_retries: int = 3) -> List[Dict]:
        """Executes an HTTP GET request to the explorer API with retries and exponential backoff."""
        if self.api_key:
            params["apikey"] = self.api_key

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{self.base_url}?{query_string}"

        for attempt in range(max_retries):
            self._rate_limit()
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Aegis3-Launch-Integrity-Agent/1.0"}
                )
                with urllib.request.urlopen(req, timeout=15) as response:
                    res_bytes = response.read()
                    data = json.loads(res_bytes.decode("utf-8"))

                    status = str(data.get("status", "0"))
                    result = data.get("result", [])

                    # Etherscan returns status='0' with result='No transactions found' when empty
                    if status == "0" and isinstance(result, str) and "No transactions" in result:
                        return []

                    if status == "1" and isinstance(result, list):
                        return result

                    # If rate limited (Max rate limit reached)
                    if isinstance(result, str) and "rate limit" in result.lower():
                        wait_time = (2 ** attempt) * 2
                        time.sleep(wait_time)
                        continue

                    return result if isinstance(result, list) else []

            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
                if attempt == max_retries - 1:
                    print(f"[EtherscanClient] Request failed after {max_retries} retries: {e}")
                    return []
                time.sleep((2 ** attempt) * 1.5)

        return []

    def get_normal_transactions(self, address: str, limit: int = 100) -> List[Dict]:
        """Fetches standard external ETH/native transactions for the address."""
        cached = self._read_cache(address, "txlist")
        if cached is not None:
            return cached

        params = {
            "module": "account",
            "action": "txlist",
            "address": address.lower().strip(),
            "startblock": "0",
            "endblock": "99999999",
            "page": "1",
            "offset": str(limit),
            "sort": "asc",
        }
        data = self._fetch_api(params)
        self._write_cache(address, "txlist", data)
        return data

    def get_token_transactions(self, address: str, limit: int = 100) -> List[Dict]:
        """Fetches ERC-20 token transfer events."""
        cached = self._read_cache(address, "tokentx")
        if cached is not None:
            return cached

        params = {
            "module": "account",
            "action": "tokentx",
            "address": address.lower().strip(),
            "startblock": "0",
            "endblock": "99999999",
            "page": "1",
            "offset": str(limit),
            "sort": "asc",
        }
        data = self._fetch_api(params)
        self._write_cache(address, "tokentx", data)
        return data
