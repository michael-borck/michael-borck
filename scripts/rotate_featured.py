#!/usr/bin/env python3
"""Rotate the featured repository in the profile README."""

from __future__ import annotations

import json
import os
import random
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
LIST = ROOT / "featured-repos.json"
START = "<!-- FEATURED:START -->"
END = "<!-- FEATURED:END -->"


def api(url: str, token: str | None) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-featured-rotation",
        },
    )
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def current_repo(text: str) -> str | None:
    start = text.find(START)
    end = text.find(END)
    if start == -1 or end == -1:
        return None
    match = re.search(
        r"https://github\.com/michael-borck/([A-Za-z0-9._-]+)",
        text[start:end],
    )
    return match.group(1) if match else None


def build_block(data: dict[str, object]) -> str:
    name = str(data.get("name") or "repository")
    url = str(data.get("html_url") or f"https://github.com/michael-borck/{name}")
    description = str(
        data.get("description") or "A project from the portfolio."
    ).replace("\n", " ").strip()
    language = str(data.get("language") or "")
    stars = int(data.get("stargazers_count") or 0)
    topics = [str(topic) for topic in (data.get("topics") or [])][:5]

    meta: list[str] = []
    if language:
        meta.append(f"`{language}`")
    if stars:
        meta.append(f"⭐ {stars}")
    meta.extend(f"`{topic}`" for topic in topics)

    return (
        f"{START}\n"
        f"### [{name}]({url})\n\n"
        f"{description}\n\n"
        f"{' · '.join(meta)}\n\n"
        f"[Explore the repository →]({url})\n"
        f"{END}"
    )


def main() -> int:
    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print("featured markers not found in README", file=sys.stderr)
        return 1

    current = current_repo(text)
    repos = json.loads(LIST.read_text(encoding="utf-8"))
    choices = [
        repo
        for repo in repos
        if not current or not str(repo).endswith("/" + current)
    ]
    if not choices:
        choices = repos

    repo = random.SystemRandom().choice(choices)
    token = os.environ.get("GITHUB_TOKEN")
    try:
        data = api(f"https://api.github.com/repos/{repo}", token)
    except Exception as error:
        print(f"metadata fetch failed for {repo}: {error}", file=sys.stderr)
        data = {
            "name": str(repo).split("/")[-1],
            "html_url": f"https://github.com/{repo}",
        }

    block = build_block(data)
    start = text.index(START)
    end = text.index(END) + len(END)
    README.write_text(text[:start] + block + text[end:], encoding="utf-8")
    print(f"featured: {repo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
