import asyncio
from urllib.parse import urljoin

from crawl4ai import AsyncWebCrawler

TARGET_PAGE_KEYWORDS = [
    "about",
    "about-us",
    "team",
    "leadership",
    "company",
    "our-story",
    "founder",
    "founders",
    "who-we-are",
]

MAX_TEXT_LENGTH = 20000


class WebsiteExtractor:

    def __init__(self):

        self.crawler = None

    async def start(self):

        self.crawler = AsyncWebCrawler()

        await self.crawler.__aenter__()

    async def close(self):

        if self.crawler:
            await self.crawler.__aexit__(
                None,
                None,
                None
            )

    async def crawl_page(self, url):

        try:

            result = await self.crawler.arun(
                url=url
            )

            if not result:
                return ""

            markdown = ""

            if hasattr(result, "markdown"):

                markdown = result.markdown

            elif hasattr(result, "markdown_v2"):

                markdown = (
                    result.markdown_v2.raw_markdown
                )

            if not markdown:
                return ""

            return markdown[:MAX_TEXT_LENGTH]

        except Exception as e:

            print(f"[CRAWL ERROR] {url} -> {e}")

            return ""

    def extract_internal_links(
        self,
        markdown,
        base_url
    ):

        found = []

        seen = set()

        lines = markdown.splitlines()

        for line in lines:

            lower = line.lower()

            for keyword in TARGET_PAGE_KEYWORDS:

                if keyword in lower:

                    if "(" in line and ")" in line:

                        try:

                            possible = (
                                line.split("(")[-1]
                                .split(")")[0]
                                .strip()
                            )

                            if possible.startswith("http"):

                                url = possible

                            else:

                                url = urljoin(
                                    base_url,
                                    possible
                                )

                            if url not in seen:

                                found.append(url)

                                seen.add(url)

                        except Exception:
                            pass

        return found[:10]

    async def scrape_website(self, website):

        result = {
            "website": website,
            "text": "",
        }

        if not website.startswith("http"):
            website = f"https://{website}"

        combined_text = ""

        homepage_markdown = await self.crawl_page(
            website
        )

        if not homepage_markdown:
            return result

        combined_text += "\n" + homepage_markdown

        internal_links = self.extract_internal_links(
            homepage_markdown,
            website
        )

        tasks = [
            self.crawl_page(link)
            for link in internal_links
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )

        for markdown in results:

            if isinstance(markdown, Exception):
                continue

            if not markdown:
                continue

            combined_text += "\n" + markdown

        result["text"] = combined_text[
            :MAX_TEXT_LENGTH
        ]

        return result
