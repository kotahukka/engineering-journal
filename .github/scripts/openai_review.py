#!/usr/bin/env python3

import json
import os
import sys
import urllib.request

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-5")

PROMPT_FILE = ".github/prompts/openai_review.md"
SECURITY_PROMPT_FILE = ".github/prompts/openai_review_security.md"


def load_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def call_openai(prompt: str) -> str:
    url = "https://api.openai.com/v1/responses"

    payload = {"model": MODEL, "input": prompt}

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return f"## Summary\n- OpenAI request failed: {e}"

    if "output_text" in data:
        return data["output_text"]

    return json.dumps(data, indent=2)[:8000]


def main():
    if not OPENAI_API_KEY:
        print("## Summary\n- OPENAI_API_KEY not configured")
        sys.exit(0)

    diff = os.environ.get("PR_DIFF", "")

    if not diff.strip():
        print("## Summary\n- No diff content provided")
        sys.exit(0)

    review_prompt = load_file(PROMPT_FILE)
    security_prompt = load_file(SECURITY_PROMPT_FILE)

    combined_prompt = f"""
{review_prompt}

---

{security_prompt}

---

PR DIFF:

{diff}
"""

    response = call_openai(combined_prompt)

    print("🤖 **AI Review (OpenAI)**\n")
    print(response)


if __name__ == "__main__":
    main()
