from __future__ import annotations

import time
from dataclasses import dataclass

import requests


@dataclass
class HttpClient:
    delay_seconds: float = 0.05
    timeout: int = 6

    def __post_init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 compatible; infant-formula-intel-poc/0.1; public-web-research"
            }
        )

    def get(self, url: str) -> requests.Response | None:
        time.sleep(self.delay_seconds)
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code >= 400:
                return None
            return resp
        except requests.RequestException:
            return None



