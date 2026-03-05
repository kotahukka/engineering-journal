#!/usr/bin/env python3

import json
import os
import sys
import urllib.request

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
MODEL = os.environ.get("OPENAI_MODEL", "gpt-5").strip()

PROMPT_FILE = os.environ.get("REVIEW_PROMPT_FILE", ".github/prompts/openai_review.md")
SEC_PROMPT_FILE = os.environ.get(
    "SECURITY_PROMPT_FILE", ".github/prompts/openai_review_security.md"
)


def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def call_openai(prompt: str) -> str:
    url = os.environ.get(
        "OPENAI_API_URL", "https://api.openai.com/v1/responses"
    ).strip()

    payload = {
        "model": MODEL,
        "input": prompt,
    }

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
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return f"## Summary\n- OpenAI request failed: {e}"

    if isinstance(data, dict) and isinstance(data.get("output_text"), str):
        return data["output_text"]

    # Best-effort fallback for varied response shapes
    try:
        out = data.get("output", [])
        texts = []
        for item in out:
            if not isinstance(item, dict):
                continue
            for c in item.get("content", []):
                if (
                    isinstance(c, dict)
                    and c.get("type") in ("output_text", "text")
                    and isinstance(c.get("text"), str)
                ):
                    texts.append(c["text"])
        if texts:
            return "\n".join(texts)
    except Exception:
        pass

    return json.dumps(data, indent=2)[:8000]


def main() -> int:
    if not OPENAI_API_KEY:
        print("## Summary\n- OPENAI_API_KEY is not configured.")
        return 0

    review_text = os.environ.get("REVIEW_TEXT", "").strip()
    if not review_text:
        print("## Summary\n- No review input provided (REVIEW_TEXT is empty).")
        return 0

    base_prompt = read_file(PROMPT_FILE)
    sec_prompt = read_file(SEC_PROMPT_FILE)

    max_chars = int(os.environ.get("MAX_REVIEW_CHARS", "140000"))
    if len(review_text) > max_chars:
        review_text = review_text[:max_chars] + "\n\n[TRUNCATED]\n"

    combined = (
        base_prompt
        + "\n\n---\n"
        + sec_prompt
        + "\n\n---\nCHANGED FILES (filtered) WITH PATCHES:\n"
        + review_text
    )

    response = call_openai(combined).strip() or "## Summary\n- No output from reviewer."

    print("🤖 **AI Review (OpenAI)**\n")
    print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
