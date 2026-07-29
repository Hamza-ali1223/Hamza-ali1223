"""Build assets/projects-dark.svg and projects-light.svg.

Concept: three specimens mounted side by side on one plate. Each card is a
recessed panel carrying the project's name, what it actually does, its stack,
its live star count, when it was last touched, and a donut of its language mix.

Two decisions worth stating:

  * Donut colours come from a palette-derived ramp (accent -> specimen -> mute
    -> mute faded toward paper), not GitHub Linguist's brand colours. Linguist's
    Java orange and TypeScript blue would fight the forest ground and undo the
    whole point of having a palette.
  * A project with `"repo": null` is a first-class case, not an error. Its card
    renders from the hand-written fields and simply omits the live row.

Reads only the `cache` block written by fetch_data.py -- never the network.
"""

import json
import math
from datetime import date
from pathlib import Path

import plate
from plate import Timeline
from theme import THEMES, mix
from typeset import fit, measure, path, wrap

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "assets"
DATA = ROOT / "projects.json"

W = 1200

# --- layout -----------------------------------------------------------------
PAD_L, PAD_R = 56, 1144
HEAD_Y, HEAD_RULE_Y = 72, 92

CARD_Y, CARD_H, GAP = 118, 264, 26
INSET = 22                       # card padding

NAME_DY, RULE_DY = 46, 62
BLURB_DY, BLURB_LEAD = 90, 18
TAGS_DY = 158
DONUT_DY, DONUT_R, DONUT_W = 206, 26, 7
LEGEND_DY, LEGEND_LEAD = 190, 17
ACTIVITY_DY = 250

FRESH_DAYS = 90                  # "recently updated" threshold


def donut_stops(t):
    """Four palette stops, brightest first -- largest language gets the accent."""
    return [t["accent"], t["specimen"], t["mute"],
            mix(t["mute"], t["paper"], 0.45)]


def star(cx, cy, r=5.0):
    """A five-pointed star as a path.

    Drawn rather than typed: JetBrains Mono has no U+2605, and typeset.outline
    renders a missing glyph as a blank advance -- so `★ 12` would silently
    become ` 12`.
    """
    pts = []
    for i in range(10):
        rad = r if i % 2 == 0 else r * 0.42
        a = i * math.pi / 5 - math.pi / 2
        pts.append(f"{cx + rad * math.cos(a):.2f} {cy + rad * math.sin(a):.2f}")
    return "M" + "L".join(pts) + "Z"


def arc(cx, cy, r, a0, a1):
    """Path for a circular arc between two angles, measured from 12 o'clock."""
    x0, y0 = cx + r * math.sin(a0), cy - r * math.cos(a0)
    x1, y1 = cx + r * math.sin(a1), cy - r * math.cos(a1)
    large = 1 if (a1 - a0) > math.pi else 0
    return (f"M{x0:.2f} {y0:.2f}A{r} {r} 0 {large} 1 {x1:.2f} {y1:.2f}")


def donut(cx, cy, langs, t, tl, begin):
    """Language mix as drawn-on arc segments.

    Each segment is its own path with its own dasharray, so draw_on animates
    them independently. The angular gap between segments also removes the
    degenerate single-language case -- a 100% arc would have start == end and
    render as nothing.
    """
    stops = donut_stops(t)
    total = sum(langs.values()) or 1
    gap = 0.06
    out, a = [], 0.0

    for i, (_, v) in enumerate(langs.items()):
        span = (v / total) * math.tau
        if span <= gap * 1.5:
            a += span
            continue
        a0, a1 = a + gap / 2, a + span - gap / 2
        out.append(tl.draw_on(arc(cx, cy, DONUT_R, a0, a1),
                              stops[min(i, len(stops) - 1)],
                              begin + i * 0.09, 0.7,
                              round(DONUT_R * (a1 - a0), 1) + 2,
                              DONUT_W, cap="butt"))
        a += span
    return out


def card(x, w, prj, t, tl, begin):
    """One specimen card."""
    line_c, line_o = t["line"]
    _, strong_o = t["line_strong"]
    ink, soft, mute = t["ink"], t["ink_soft"], t["mute"]
    inner = w - INSET * 2
    tx = x + INSET

    p = [tl.group(
        f'<rect x="{x}" y="{CARD_Y}" width="{w}" height="{CARD_H}" '
        f'fill="{t["paper_deep"]}" stroke="{line_c}" stroke-opacity="{line_o}" '
        f'stroke-width="1"/>', begin, 0.7)]

    cache = prj.get("cache", {})

    # Name, with the star count parked on the same baseline.
    stars = cache.get("stars")
    star_w = 0.0
    if stars is not None:
        count = str(stars)
        count_w = measure(count, "mono", 11, 0.2)
        star_w = count_w + 26
        p.append(tl.mono(count, x + w - INSET, CARD_Y + NAME_DY, 11, mute,
                         begin + 0.35, anchor="end", track=0.2))
        p.append(tl.group(
            f'<path d="{star(x + w - INSET - count_w - 11, CARD_Y + NAME_DY - 4)}" '
            f'fill="{mute}"/>', begin + 0.35, 0.5))

    name = fit(prj.get("name", ""), "fraunces", 26, inner - star_w,
               opsz=144, wght=600, WONK=1)
    p.append(tl.group(
        path(name, "fraunces", 26, tx, CARD_Y + NAME_DY, fill=ink,
             opsz=144, wght=600, WONK=1),
        begin + 0.2, 0.6))
    p.append(tl.rule(tx, CARD_Y + RULE_DY, x + w - INSET, line_c, strong_o,
                     begin + 0.3, 0.6))

    # What it does.
    for i, ln in enumerate(wrap(prj.get("blurb", ""), "mono", 11, inner, 0.1,
                                max_lines=3)):
        p.append(tl.mono(ln, tx, CARD_Y + BLURB_DY + i * BLURB_LEAD, 11, soft,
                         begin + 0.4 + i * 0.06, track=0.1))

    p.append(tl.mono("  ·  ".join(prj.get("tags", [])), tx, CARD_Y + TAGS_DY,
                     10, mute, begin + 0.6, track=0.5))

    # Language mix. Live byte counts when we have them, hand-declared
    # percentages otherwise -- both normalise the same way.
    langs = cache.get("languages") or prj.get("languages") or {}
    if langs:
        cx, cy = tx + DONUT_R + 4, CARD_Y + DONUT_DY
        p += donut(cx, cy, langs, t, tl, begin + 0.7)

        stops = donut_stops(t)
        total = sum(langs.values()) or 1
        lx = cx + DONUT_R + 22
        for i, (nm, v) in enumerate(list(langs.items())[:3]):
            ly = CARD_Y + LEGEND_DY + i * LEGEND_LEAD
            p.append(tl.group(
                f'<rect x="{lx}" y="{ly - 6}" width="6" height="6" '
                f'fill="{stops[min(i, len(stops) - 1)]}"/>',
                begin + 0.85 + i * 0.06, 0.4))
            p.append(tl.mono(fit(nm, "mono", 10, 108, 0.3), lx + 13, ly, 10,
                             soft, begin + 0.85 + i * 0.06, track=0.3))
            p.append(tl.mono(f"{v / total * 100:.0f}%", x + w - INSET, ly, 10,
                             mute, begin + 0.85 + i * 0.06, anchor="end",
                             track=0.3))

    # Activity. Accent only when it is genuinely recent -- an always-on green
    # dot is decoration, not information.
    pushed = cache.get("pushed_at")
    if pushed:
        fresh = (date.today() - date.fromisoformat(pushed)).days <= FRESH_DAYS
        colour = t["accent"] if fresh else mute
        p.append(tl.group(
            f'<circle cx="{tx + 3}" cy="{CARD_Y + ACTIVITY_DY - 4}" r="3.5" '
            f'fill="{colour}"/>', begin + 1.0, 0.4))
        p.append(tl.mono(f"UPDATED  {pushed}", tx + 16, CARD_Y + ACTIVITY_DY,
                         10, colour, begin + 1.0, track=0.6))
    else:
        p.append(tl.mono("NO PUBLIC REPOSITORY", tx, CARD_Y + ACTIVITY_DY, 10,
                         mute, begin + 1.0, track=0.6))

    return p


def build(name, doc):
    projects = doc.get("projects", [])
    n = max(len(projects), 1)
    card_w = (PAD_R - PAD_L - GAP * (n - 1)) / n

    foot_rule_y = CARD_Y + CARD_H + 24
    foot_y = foot_rule_y + 26
    h = foot_y + 40

    last = 0.75 + (n - 1) * 0.22
    foot_begin = last + 1.25
    tl = Timeline(round(foot_begin + 0.95, 2))

    t = THEMES[name]
    uid = "p" + name[0]

    p = [plate.open_svg(
        W, h,
        "Projects — Hamza Ali",
        f"A specimen plate of {n} backend projects, each card carrying its "
        f"description, stack, star count, language mix and last activity.",
        "Projects: " + ", ".join(x.get("name", "") for x in projects),
    )]
    p += plate.ground(t, tl, uid, W, h)
    p += plate.header(t, tl, "§ 02", "PLATE III  ·  WORK", PAD_L, PAD_R,
                      HEAD_Y, HEAD_RULE_Y)

    for i, prj in enumerate(projects):
        x = PAD_L + i * (card_w + GAP)
        p += card(round(x, 1), round(card_w, 1), prj, t, tl, 0.75 + i * 0.22)

    p += plate.footer(t, tl, doc.get("figure", "fig. 3"), PAD_L, PAD_R,
                      foot_rule_y, foot_y, foot_begin)
    p.append("</svg>")
    return "".join(x for x in p if x)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    doc = json.loads(DATA.read_text(encoding="utf-8"))
    print(f"  {len(doc.get('projects', []))} project(s)")

    for theme in ("dark", "light"):
        svg = build(theme, doc)
        dest = OUT / f"projects-{theme}.svg"
        dest.write_text(svg, encoding="utf-8")
        print(f"  wrote {dest.name}  {len(svg) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
