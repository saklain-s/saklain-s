#!/usr/bin/env python3
"""Generate a simple SVG showing top languages across all public repos for the owner.
Writes output to assets/languages.svg

Designed to run in GitHub Actions with GITHUB_TOKEN available.
"""
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError

OWNER = os.environ.get("GITHUB_REPOSITORY", "saklain-s").split("/")[0]
API = "https://api.github.com"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"User-Agent": "generate-languages-script"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"


def get_json(url):
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except HTTPError as e:
        print(f"HTTP error fetching {url}: {e.code} {e.reason}")
        return None


def list_repos(owner):
    repos = []
    page = 1
    while True:
        url = f"{API}/users/{owner}/repos?per_page=100&page={page}"
        data = get_json(url)
        if not data:
            break
        repos.extend([r for r in data if not r.get("fork")])
        if len(data) < 100:
            break
        page += 1
    return repos


def aggregate_languages(owner):
    counts = {}
    repos = list_repos(owner)
    if not repos:
        print("No repositories found or API error.")
        return counts

    for r in repos:
        name = r["name"]
        url = f"{API}/repos/{owner}/{name}/languages"
        data = get_json(url)
        if not data:
            continue
        for lang, bytes_count in data.items():
            counts[lang] = counts.get(lang, 0) + bytes_count
    return counts


def make_svg(lang_counts, top_n=6, out_path="assets/languages.svg"):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    total = sum(lang_counts.values())
    langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]

    # Colors for a few languages; fallback to gray
    COLORS = {
        "Java": "#ED8B00",
        "Python": "#3776AB",
        "JavaScript": "#F7DF1E",
        "TypeScript": "#3178C6",
        "Go": "#00ADD8",
        "C++": "#00599C",
        "C": "#555555",
        "Shell": "#89e051",
        "HTML": "#E34F26",
    }

    width = 600
    bar_height = 18
    padding = 10
    height = padding * 2 + (bar_height + 6) * len(langs) + 30
    svg_lines = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
                 '<style>text{font-family:Inter,Arial,Helvetica,sans-serif;font-size:12px;fill:#111}</style>',
                 f'<rect width="100%" height="100%" fill="#fff" rx="6"/>',
                 f'<text x="{padding}" y="20">Top languages for {OWNER}</text>']

    y = 40
    for lang, count in langs:
        pct = (count / total) * 100 if total else 0
        w = int((width - 200) * (pct / 100))
        color = COLORS.get(lang, "#6B7280")
        svg_lines.append(f'<rect x="{padding}" y="{y}" width="{w}" height="{bar_height}" rx="4" fill="{color}" />')
        svg_lines.append(f'<text x="{padding + w + 12}" y="{y + bar_height - 4}">{lang} — {pct:.1f}%</text>')
        y += bar_height + 6

    svg_lines.append('</svg>')

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_lines))
    print(f"Wrote {out_path}")


def main():
    counts = aggregate_languages(OWNER)
    if not counts:
        # create a placeholder SVG to avoid broken image
        make_svg({"Unknown": 1}, out_path="assets/languages.svg")
        sys.exit(0)
    make_svg(counts, out_path="assets/languages.svg")


if __name__ == "__main__":
    main()
