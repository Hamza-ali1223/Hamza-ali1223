"""Refresh the live GitHub data cached in contributions.json and projects.json.

The panels never call the API themselves. This script writes a `cache` block
into each entry and the builders read only from that, which means:

  * a build with no network still produces complete, correct-looking panels;
  * a GitHub outage or a rate limit cannot blank the board.

Failure policy follows from that: every request failure is a warning, the
affected entry keeps its previous cache, and the script exits 0. The only way
this fails the workflow is a malformed JSON file, which is a real bug.

Stdlib only -- the sole third-party dependency in this repo stays fonttools.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
API = "https://api.github.com"

warnings = []


def api(path):
    """GET an API path. Returns parsed JSON, or None on any failure."""
    req = urllib.request.Request(
        f"{API}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Hamza-ali1223-profile-panels",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    # Anonymous is 60 requests/hour, authenticated is 5000. The workflow always
    # has a token; a local run usually does not, and 8-ish requests fits either.
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = "rate limited" if e.code in (403, 429) else f"HTTP {e.code}"
        warnings.append(f"{path}: {detail}")
    except Exception as e:                                # noqa: BLE001
        warnings.append(f"{path}: {type(e).__name__}: {e}")
    return None


def day(ts):
    """ISO timestamp -> YYYY-MM-DD. The panels never show a time of day."""
    return ts.split("T")[0] if ts else None


def refresh_contributions(doc):
    for c in doc.get("contributions", []):
        repo, num = c.get("repo"), c.get("pr")
        pr = api(f"/repos/{repo}/pulls/{num}")
        if not pr:
            print(f"  ~ {repo}#{num}  kept cache")
            continue

        state = "merged" if pr.get("merged") else pr.get("state", "open")
        c["cache"] = {
            "title": pr.get("title", ""),
            "state": state,
            "additions": pr.get("additions", 0),
            "deletions": pr.get("deletions", 0),
            "changed_files": pr.get("changed_files", 0),
            "merged_at": day(pr.get("merged_at")) or day(pr.get("created_at")),
        }
        print(f"  + {repo}#{num}  {state}  "
              f"+{c['cache']['additions']}/-{c['cache']['deletions']}")


def refresh_projects(doc):
    for p in doc.get("projects", []):
        slug = p.get("repo")
        if not slug:
            # Deliberate: a project with no public repo. Its card renders from
            # the hand-written fields, so there is nothing to fetch.
            print(f"  · {p.get('name')}  no public repo, static card")
            continue

        meta = api(f"/repos/{slug}")
        if not meta:
            print(f"  ~ {slug}  kept cache")
            continue

        cache = {
            "stars": meta.get("stargazers_count", 0),
            "forks": meta.get("forks_count", 0),
            "pushed_at": day(meta.get("pushed_at")),
            "url": meta.get("html_url"),
        }
        langs = api(f"/repos/{slug}/languages")
        if langs:
            # Keep the top few; the donut is 52px across and cannot show a tail.
            top = sorted(langs.items(), key=lambda kv: -kv[1])[:4]
            cache["languages"] = dict(top)

        p["cache"] = cache
        print(f"  + {slug}  ★{cache['stars']}  pushed {cache['pushed_at']}")


def load(name):
    path = ROOT / name
    return path, json.loads(path.read_text(encoding="utf-8"))


def save(path, doc):
    path.write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main():
    # PR titles and the star glyph below are arbitrary Unicode; a Windows
    # console defaults to cp1252 and would raise on them mid-run.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    if not (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")):
        print("  (no GITHUB_TOKEN -- anonymous, 60 req/hr)")

    for name, refresh in (
        ("contributions.json", refresh_contributions),
        ("projects.json", refresh_projects),
    ):
        path, doc = load(name)
        print(f"{name}:")
        refresh(doc)
        save(path, doc)

    if warnings:
        print(f"\n{len(warnings)} request(s) failed; those entries kept their "
              f"cached values:", file=sys.stderr)
        for w in warnings:
            print(f"  ! {w}", file=sys.stderr)

    # Always 0. A stale panel beats a failed build.
    return 0


if __name__ == "__main__":
    sys.exit(main())
