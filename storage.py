import asyncio
import csv
import os
from urllib.parse import quote, urlparse

import psycopg
from psycopg.rows import dict_row

RESULTS_FILE = "output/results.csv"
FAILED_FILE = "output/failed.csv"

RESULTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS scrape_results (
    id BIGSERIAL PRIMARY KEY,
    website TEXT NOT NULL,
    role TEXT NOT NULL,
    full_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""

FAILED_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS scrape_failed (
    id BIGSERIAL PRIMARY KEY,
    website TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""


class ResultStore:

    def __init__(self):

        self.mode = "csv"
        self.conn = None
        self.lock = asyncio.Lock()

    def _has_supabase_config(self):

        return all([
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_DB_PASSWORD"),
        ])

    def _build_dsn(self):

        supabase_url = os.getenv("SUPABASE_URL", "").strip()
        password = os.getenv("SUPABASE_DB_PASSWORD", "").strip()

        parsed = urlparse(supabase_url)
        host = parsed.hostname or ""

        if not host:
            raise RuntimeError("SUPABASE_URL is invalid")

        if not host.startswith("db."):
            host = f"db.{host}"

        encoded_password = quote(password, safe="")

        return (
            f"postgresql://postgres:{encoded_password}"
            f"@{host}:5432/postgres?sslmode=require"
        )

    async def start(self):

        if self._has_supabase_config():

            self.mode = "supabase"
            dsn = self._build_dsn()
            self.conn = await psycopg.AsyncConnection.connect(dsn)
            self.conn.autocommit = True
            await self._ensure_schema()
            return

        self.mode = "csv"
        self._ensure_csv_files()

    async def close(self):

        if self.conn:
            await self.conn.close()
            self.conn = None

    def _ensure_csv_files(self):

        os.makedirs("output", exist_ok=True)

        if not os.path.exists(RESULTS_FILE):

            with open(RESULTS_FILE, "w", newline="") as f:

                writer = csv.writer(f)
                writer.writerow(["website", "role", "full_name"])

        if not os.path.exists(FAILED_FILE):

            with open(FAILED_FILE, "w", newline="") as f:

                writer = csv.writer(f)
                writer.writerow(["website"])

    async def _ensure_schema(self):

        async with self.lock:

            await self.conn.execute(RESULTS_TABLE_SQL)
            await self.conn.execute(FAILED_TABLE_SQL)

    async def append_result(self, website, role, full_name):

        if self.mode == "supabase":

            async with self.lock:

                await self.conn.execute(
                    """
                    INSERT INTO scrape_results (website, role, full_name)
                    VALUES (%s, %s, %s)
                    """,
                    (website, role, full_name),
                )

            return

        self._ensure_csv_files()

        with open(RESULTS_FILE, "a", newline="") as f:

            writer = csv.writer(f)
            writer.writerow([website, role, full_name])

    async def append_failed(self, website):

        if self.mode == "supabase":

            async with self.lock:

                await self.conn.execute(
                    """
                    INSERT INTO scrape_failed (website)
                    VALUES (%s)
                    """,
                    (website,),
                )

            return

        self._ensure_csv_files()

        with open(FAILED_FILE, "a", newline="") as f:

            writer = csv.writer(f)
            writer.writerow([website])

    async def load_completed_websites(self):

        if self.mode == "supabase":

            async with self.lock:

                async with self.conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(
                        "SELECT DISTINCT website FROM scrape_results"
                    )
                    rows = await cur.fetchall()

            return {
                row["website"]
                for row in rows
            }

        completed = set()

        if not os.path.exists(RESULTS_FILE):
            return completed

        with open(RESULTS_FILE, "r") as f:

            reader = csv.DictReader(f)

            for row in reader:
                completed.add(row["website"])

        return completed


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
