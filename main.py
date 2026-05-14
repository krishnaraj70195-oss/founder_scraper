import asyncio
import sys

from extractor import WebsiteExtractor
from analyzer import LeadershipAnalyzer

from storage import (
    initialize_storage,
    close_storage,
    append_result,
    append_failed,
    load_completed_websites,
    load_websites,
)

CONCURRENCY = 30

MAX_CONSECUTIVE_FAILURES = 50

consecutive_failures = 0


async def process_website(
    website,
    extractor,
    analyzer,
    semaphore
):

    global consecutive_failures

    async with semaphore:

        print(f"[SCRAPING] {website}")

        try:

            extracted = await extractor.scrape_website(
                website
            )

            text = extracted["text"]

            if not text:

                consecutive_failures += 1

                print(
                    f"[NO TEXT] {website} "
                    f"(Failures: {consecutive_failures})"
                )

                await append_failed(website)

                check_failure_limit()

                return

            people = await analyzer.analyze(text)

            if not people:

                consecutive_failures += 1

                print(
                    f"[NO PEOPLE] {website} "
                    f"(Failures: {consecutive_failures})"
                )

                await append_failed(website)

                check_failure_limit()

                return

            for person in people:

                await append_result(
                    website,
                    person["role"],
                    person["full_name"]
                )

            consecutive_failures = 0

            print(
                f"[SUCCESS] {website} "
                f"({len(people)} people)"
            )

        except Exception as e:

            consecutive_failures += 1

            print(
                f"[ERROR] {website} -> {e} "
                f"(Failures: {consecutive_failures})"
            )

            await append_failed(website)

            check_failure_limit()


def check_failure_limit():

    global consecutive_failures

    if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:

        print("\n")
        print("=" * 60)
        print("TOO MANY CONSECUTIVE FAILURES")
        print("Possible:")
        print("- Rate limiting")
        print("- IP blocking")
        print("- Browser failure")
        print("- Internet issue")
        print("- Crawl4AI degradation")
        print("=" * 60)
        print("\n")

        sys.exit(1)


async def main():

    await initialize_storage()

    websites = await load_websites()

    if not websites:
        print("No websites found in Supabase table scrape_websites")
        await close_storage()
        return

    completed = await load_completed_websites()

    websites = [
        w for w in websites
        if w not in completed
    ]

    print(f"Remaining websites: {len(websites)}")

    extractor = WebsiteExtractor()

    analyzer = LeadershipAnalyzer()

    await extractor.start()

    semaphore = asyncio.Semaphore(CONCURRENCY)

    tasks = []

    for website in websites:

        task = process_website(
            website,
            extractor,
            analyzer,
            semaphore
        )

        tasks.append(task)

    await asyncio.gather(*tasks)

    await extractor.close()
    await close_storage()

    print("DONE")


if __name__ == "__main__":
    asyncio.run(main())
