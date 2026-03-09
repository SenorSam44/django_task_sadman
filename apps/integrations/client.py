import logging
import time
from typing import List, Dict, Optional
from requests import Session, Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class BookingSystemClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/') + '/index.php/api/v1'
        self.session = Session()
        self.session.auth = (username, password)
        retry_strategy = Retry(
            total=3,
            status_forcelist=[500, 502, 503, 504],
            backoff_factor=1,  # 1,2,4s
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, json: Optional[Dict] = None) -> Response:
        url = f"{self.base_url}/{endpoint}"
        start = time.time()
        try:
            resp = self.session.request(method, url, params=params, json=json, timeout=10)
            duration = time.time() - start
            logger.info("API call", method=method, url=url, status=resp.status_code, duration=duration)
            if resp.status_code == 429:
                logger.warning("Rate limited", url=url)
                time.sleep(30)
                return self._request(method, endpoint, params, json)  # Retry once
            resp.raise_for_status()
            return resp
        except Exception as e:
            logger.error("API error", exc_info=e)
            raise

    def test_connection(self) -> bool:
        try:
            self._request('GET', 'services', params={'length': 1})
            return True
        except:
            return False

    def _get_all(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
        params = params or {}
        params['length'] = 100  # Larger page size
        page = 1
        results = []
        while True:
            params['page'] = page
            resp = self._request('GET', endpoint, params=params)
            data = resp.json()
            if not data:
                break
            results.extend(data)
            page += 1
        return results

    def get_providers(self) -> List[dict]:
        return self._get_all('providers')

    def get_customers(self) -> List[dict]:
        return self._get_all('customers')

    def get_services(self) -> List[dict]:
        return self._get_all('services')

    def get_appointments(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[dict]:
        params = {}
        if start_date:
            params['from'] = start_date
        if end_date:
            params['till'] = end_date
        return self._get_all('appointments', params=params)

