import logging
import time
from typing import List, Dict, Optional

from requests import Session, Response
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 100
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3


class BookingSystemClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/") + "/index.php/api/v1"

        self.session = Session()
        self.session.auth = (username, password)

        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=1,  # exponential backoff: 1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)

        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ) -> Response:
        """Internal helper for making API requests with logging and error handling."""
        url = f"{self.base_url}/{endpoint}"

        start_time = time.time()

        try:
            response = self.session.request(
                method,
                url,
                params=params,
                json=json,
                timeout=REQUEST_TIMEOUT,
            )

            duration = time.time() - start_time

            logger.info(
                "API %s %s -> %s (%.2fs)",
                method,
                url,
                response.status_code,
                duration,
            )

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 5))
                logger.warning(
                    "Rate limited on %s. Sleeping for %s seconds",
                    url,
                    retry_after,
                )
                time.sleep(retry_after)

            response.raise_for_status()

            return response

        except RequestException as exc:
            logger.error("Request failed for %s: %s", url, str(exc))
            raise

    def test_connection(self) -> bool:
        """Verify credentials work."""
        try:
            self._request("GET", "services", params={"length": 1})
            return True
        except Exception:
            return False

    def _get_all(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
    ) -> List[Dict]:
        """Fetch all results from a paginated endpoint."""
        params = dict(params or {})
        params["length"] = DEFAULT_PAGE_SIZE

        page = 1
        results: List[Dict] = []

        while True:
            params["page"] = page
            response = self._request("GET", endpoint, params=params)
            data = response.json()
            if not data:
                break

            results.extend(data)

            if len(data) < DEFAULT_PAGE_SIZE:
                break

            page += 1
        return results

    def get_providers(self) -> List[Dict]:
        """Fetch all providers."""
        return self._get_all("providers")

    def get_customers(self) -> List[Dict]:
        """Fetch all customers."""
        return self._get_all("customers")

    def get_services(self) -> List[Dict]:
        """Fetch all services."""
        return self._get_all("services")

    def get_appointments(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """Fetch appointments, optionally filtered by date range."""
        params: Dict[str, str] = {}

        if start_date:
            params["from"] = start_date

        if end_date:
            params["till"] = end_date

        return self._get_all("appointments", params=params)
