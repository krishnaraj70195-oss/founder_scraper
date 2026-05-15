import re

from dotenv import load_dotenv
from openai import AsyncOpenAI

from prompts import SYSTEM_PROMPT, build_user_prompt

load_dotenv()

MODEL = "gpt-4.1-mini"

client = AsyncOpenAI()


class LeadershipAnalyzer:

    def __init__(self):
        pass

    async def analyze(self, text):

        if not text.strip():
            print("[EMPTY TEXT]")
            return []

        try:

            response = await client.chat.completions.create(
                model=MODEL,
                temperature=0,
                max_tokens=120,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": build_user_prompt(text)
                    }
                ]
            )

            output = response.choices[0].message.content.strip()

            return self.parse_output(output)

        except Exception as e:

            print(f"[AI ERROR] {e}")

            return []

    def parse_output(self, output):

        if output.upper() == "NONE":
            return []

        results = []

        seen = set()

        lines = output.splitlines()

        for line in lines:

            if "|" not in line:
                continue

            parts = line.split("|", 1)

            if len(parts) != 2:
                print("[BAD SPLIT]")
                continue

            role = parts[0].strip()
            name = parts[1].strip()

            role_lower = role.lower()

            valid_role = any(
                keyword in role_lower
                for keyword in [
                    "founder",
                    "co-founder",
                    "ceo",
                    "owner",
                    "co-owner",
                ]
            )

            if not valid_role:
                continue

            if not self.is_valid_name(name):
                continue

            key = f"{role}-{name.lower()}"

            if key in seen:
                continue

            seen.add(key)

            results.append({
                "role": role,
                "full_name": name
            })

        return results

    def is_valid_name(self, name):

        if not name:
            return False

        lower = name.lower().strip()

        invalid_exact = [
            "none",
            "unknown",
            "n/a",
        ]

        if lower in invalid_exact:
            return False

        invalid_contains = [
            "agency",
            "services",
            "solutions",
            "marketing",
            "media",
            "group",
            "team",
            "company",
            "contractors",
            "clinic",
            "healthcare",
            "studio",
            "works",
            "digital",
            "creative",
            "design",
            "branding",
            "labs",
            "lab",
            "technologies",
            "technology",
            "systems",
            "software",
            "inc",
            "llc",
            "ltd",
            "corp",
            "co.",
        ]

        if any(word in lower for word in invalid_contains):
            return False

        if len(name) > 40:
            return False

        if len(name.split()) > 5:
            return False

        if any(char.isdigit() for char in name):
            return False

        if "@" in name:
            return False

        if ".com" in lower:
            return False

        words = name.split()

        # SINGLE NAME SUPPORT
        if len(words) == 1:

            word = words[0]

            if not word[0].isupper():
                return False

            if len(word) < 3:
                return False

            return True

        # MULTI-WORD NAMES
        capitalized_words = 0

        for word in words:

            if word[:1].isupper():
                capitalized_words += 1

        if capitalized_words == 0:
            return False

        return True
