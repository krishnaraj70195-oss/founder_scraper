import asyncio
import json
import os
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

RESULTS_TABLE = "scrape_results"
FAILED_TABLE = "scrape_failed"
WEBSITES_TABLE = "scrape_websites"


class ResultStore:

    def __init__(self):

        self.base_url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.api_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

    def _headers(self):

        if not self.base_url or not self.api_key:
            raise RuntimeError("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing")

        return {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def _request(self, method, path, params=None, body=None):

        url = f"{self.base_url}/rest/v1/{path}"

        if params:
            url = f"{url}?{urlencode(params)}"

        data = None

        if body is not None:
            data = json.dumps(body).encode("utf-8")

        req = Request(
            url,
            data=data,
            headers=self._headers(),
            method=method,
        )

        with urlopen(req, timeout=120) as resp:
            payload = resp.read().decode("utf-8")
            return json.loads(payload) if payload else []

    async def start(self):

        if not self.base_url or not self.api_key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required"
            )

    async def close(self):

        return None

    async def append_result(self, website, role, full_name):

        await asyncio.to_thread(
            self._request,
            "POST",
            RESULTS_TABLE,
            None,
            {
                "website": website,
                "role": role,
                "full_name": full_name,
            },
        )

    async def append_failed(self, website):

        await asyncio.to_thread(
            self._request,
            "POST",
            FAILED_TABLE,
            None,
            {
                "website": website,
            },
        )

    async def load_completed_websites(self):

        rows = await asyncio.to_thread(
            self._request,
            "GET",
            RESULTS_TABLE,
            {
                "select": "website",
            },
            None,
        )

        return {
            row["website"]
            for row in rows
            if row.get("website")
        }

    async def load_websites(self):

        rows = await asyncio.to_thread(
            self._request,
            "GET",
            WEBSITES_TABLE,
            {
                "select": "website",
            },
            None,
        )

        return [
            row["website"]
            for row in rows
            if row.get("website")
        ]


store = ResultStore()


async def initialize_storage():

    await store.start()


async def close_storage():

    await store.close()


async def append_result(website, role, full_name):

    await store.append_result(website, role, full_name)


async def append_failed(website):

    await store.append_failed(website)


async def load_completed_websites():

    return await store.load_completed_websites()


async def load_websites():

    return await store.load_websites()
