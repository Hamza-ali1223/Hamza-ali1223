"""Build assets/stats-dark.svg and stats-light.svg.

This plate exists because the third-party cards it replaces stopped working.
github-readme-stats' public Vercel deployment answers 503 DEPLOYMENT_PAUSED
whenever it trips the free tier, which takes the stats card and the top-languages
card down with it and leaves two broken images in the README. Pointing at a
community mirror only moves the dependency; generating the plate here removes it.

Everything shown is reachable from the REST API without a token, so a local run
produces the same plate CI does. Figures on the left, language mix on the right,
divided by a rule -- same plate language as the other three.

Reads only the `cache` block written by fetch_data.py -- never the network.
"""

import json
from pathlib import Path

import plate
from plate import Timeline
from theme import THEMES, ramp
from typeset import fit, measure, path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "assets"
DATA = ROOT / "stats.json"

W, H = 1200, 380

# --- layout -----------------------------------------------------------------
PAD_L, PAD_R = 56, 1144
HEAD_Y, HEAD_RULE_Y = 72, 92
FOOT_RULE_Y, FOOT_Y = 314, 340

DIVIDER_X = 608
COL_X = (56, 246, 436)           # three figure columns
FIG_Y = (186, 268)               # numeral baselines, two rows
LABEL_DY = 20                    # label sits this far under its numeral

CHART_X = 648
CHART_LABEL_Y = 150
BAR_Y, BAR_W = 178, 12
LEGEND_Y, LEGEND_LEAD = 196, 18


def figures(cache):
    """The six cells, in reading order. Falls back to em-dash when unknown."""
    def v(key):
        n = cache.get(key)
        return "—" if n is None else f"{n:,}"

    return [
        (v("public_repos"), "PUBLIC REPOS"),
        (v("stars"),        "STARS EARNED"),
        (v("followers"),    "FOLLOWERS"),
        (v("prs"),          "PULL REQUESTS"),
        (v("prs_merged"),   "MERGED UPSTREAM"),
        (cache.get("since") or "—", "ON GITHUB SINCE"),
    ]


def build(name, doc):
    t = THEMES[name]
    line_c, line_o = t["line"]
    _, strong_o = t["line_strong"]
    ink, soft, mute = t["ink"], t["ink_soft"], t["mute"]
    uid = "s" + name[0]

    cache = doc.get("cache") or {}
    tl = Timeline(3.4)

    p = [plate.open_svg(
        W, H,
        "By the numbers — Hamza Ali",
        "A plate tallying public repositories, stars, followers and pull "
        "requests, alongside a bar of the language mix across all repositories.",
        "GitHub statistics and language mix for Hamza Ali",
    )]
    p += plate.ground(t, tl, uid, W, H)
    p += plate.header(t, tl, "§ 05", "PLATE IV  ·  TALLY", PAD_L, PAD_R,
                      HEAD_Y, HEAD_RULE_Y)

    # --- figures -----------------------------------------------------------
    for i, (value, label) in enumerate(figures(cache)):
        x = COL_X[i % 3]
        y = FIG_Y[i // 3]
        b = 0.7 + i * 0.11
        p.append(tl.group(
            path(value, "fraunces", 44, x, y, fill=ink,
                 opsz=144, wght=600, WONK=1),
            b, 0.6))
        p.append(tl.mono(label, x, y + LABEL_DY, 10, mute, b + 0.12, track=0.6))

    # Divider between the tally and the chart.
    p.append(tl.draw_on(f"M{DIVIDER_X} 130V300", line_c, 0.6, 0.9, 170, 1,
                        strong_o, cap="butt"))

    # --- language mix ------------------------------------------------------
    langs = cache.get("languages") or {}
    if langs:
        stops = ramp(t, len(langs))
        total = sum(langs.values()) or 1

        p.append(tl.mono("TOP LANGUAGES  ·  BY BYTES WRITTEN", CHART_X,
                         CHART_LABEL_Y, 11, mute, 1.25, track=0.6))

        # One stacked bar, drawn as thick line segments so draw_on can reveal
        # each language in turn. A donut would repeat plate III.
        bar_w = PAD_R - CHART_X
        x = CHART_X
        for i, (nm, v) in enumerate(langs.items()):
            seg = bar_w * v / total
            if seg < 1:
                continue
            p.append(tl.draw_on(f"M{x:.1f} {BAR_Y}H{x + seg:.1f}",
                                stops[min(i, len(stops) - 1)],
                                1.4 + i * 0.1, 0.75, round(seg, 1) + 2,
                                BAR_W, cap="butt"))
            x += seg

        for i, (nm, v) in enumerate(langs.items()):
            ly = LEGEND_Y + i * LEGEND_LEAD
            b = 1.9 + i * 0.09
            p.append(tl.group(
                f'<rect x="{CHART_X}" y="{ly - 7}" width="7" height="7" '
                f'fill="{stops[min(i, len(stops) - 1)]}"/>', b, 0.4))
            p.append(tl.mono(fit(nm, "mono", 11, 300, 0.2), CHART_X + 15, ly,
                             11, soft, b, track=0.2))
            p.append(tl.mono(f"{v / total * 100:.1f}%", PAD_R, ly, 11, mute, b,
                             anchor="end", track=0.2))
    else:
        p.append(tl.mono("LANGUAGE MIX UNAVAILABLE", CHART_X, CHART_LABEL_Y, 11,
                         mute, 1.25, track=0.6))

    p += plate.footer(t, tl, doc.get("figure", "fig. 4"), PAD_L, PAD_R,
                      FOOT_RULE_Y, FOOT_Y, 2.35)
    p.append("</svg>")
    return "".join(x for x in p if x)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    doc = json.loads(DATA.read_text(encoding="utf-8"))
    cache = doc.get("cache") or {}
    if not cache:
        print("  ! stats.json has no cache -- run fetch_data.py first")

    # Widest numeral decides whether the three columns can hold their figures.
    widest = max((measure(v, "fraunces", 44, opsz=144, wght=600, WONK=1)
                  for v, _ in figures(cache)), default=0)
    print(f"  widest figure -> {widest:.0f}px (column is 190px)")

    for theme in ("dark", "light"):
        svg = build(theme, doc)
        dest = OUT / f"stats-{theme}.svg"
        dest.write_text(svg, encoding="utf-8")
        print(f"  wrote {dest.name}  {len(svg) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
