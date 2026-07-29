"""Build assets/contributions-dark.svg and contributions-light.svg.

Concept: the banner's specimen plate showed one system branching into its own
services. This plate shows the opposite direction -- work leaving, grafted onto
somebody else's trunk. The upstream repository is the stock; each merged pull
request is a graft taken off it.

The layout is a generalisation of the banner's hardcoded BRANCHES list: rows are
computed from however many entries contributions.json holds, and the panel grows
taller rather than denser, so two contributions and eight both look deliberate.

Reads only the `cache` block written by fetch_data.py -- never the network.
"""

import json
from pathlib import Path

import plate
from plate import Timeline
from theme import THEMES
from typeset import fit, measure

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "assets"
DATA = ROOT / "contributions.json"

W = 1200

# --- layout -----------------------------------------------------------------
PAD_L, PAD_R = 56, 1144
HEAD_Y, HEAD_RULE_Y = 72, 92

ROOT_X, JUNCTION_X = 150, 300
NODE_X, TEXT_X = 430, 452

BODY_TOP = 120
ROW_H = 76
NODE_DY = 26          # node offset from the top of its row
TITLE_DY, TAGS_DY = 26, 45   # baselines relative to the node


def row_y(i):
    return BODY_TOP + ROW_H * i + NODE_DY


def dots(x1, x2, y, colour, op, tl, begin):
    """A dotted leader.

    Deliberately faded in rather than drawn on: draw_on works by animating
    stroke-dashoffset against a stroke-dasharray, and this line needs its
    dasharray for the dots themselves.
    """
    if x2 - x1 < 12:
        return ""
    return tl.group(
        f'<path d="M{x1} {y}H{x2}" stroke="{colour}" stroke-opacity="{op}" '
        f'stroke-width="1" stroke-dasharray="1 5" stroke-linecap="round"/>',
        begin, 0.5)


def build(name, doc):
    items = doc.get("contributions", [])
    n = max(len(items), 1)

    body_h = n * ROW_H
    foot_rule_y = BODY_TOP + body_h + 22
    foot_y = foot_rule_y + 26
    h = foot_y + 40

    ys = [row_y(i) for i in range(n)]
    axis_y = sum(ys) / len(ys)

    # One shared timeline sized to fit however many rows there are.
    last = 1.25 + (n - 1) * 0.16
    foot_begin = last + 1.15
    tl = Timeline(round(foot_begin + 0.95, 2))

    t = THEMES[name]
    line_c, line_o = t["line"]
    _, strong_o = t["line_strong"]
    soft, mute, accent = t["ink_soft"], t["mute"], t["accent"]
    spec = t["specimen"]
    uid = "c" + name[0]

    merged = sum(1 for c in items if c.get("cache", {}).get("state") == "merged")

    p = [plate.open_svg(
        W, h,
        "Open source contributions — Hamza Ali",
        f"A specimen plate showing {n} pull request(s) grafted onto upstream "
        f"repositories, {merged} of them merged.",
        f"Open source contributions: {n} pull requests, {merged} merged",
    )]
    p += plate.ground(t, tl, uid, W, h)
    p += plate.header(t, tl, "§ 01", "PLATE II  ·  UPSTREAM", PAD_L, PAD_R,
                      HEAD_Y, HEAD_RULE_Y)

    # --- the stock ---------------------------------------------------------
    p.append(tl.draw_on(
        f"M{ROOT_X} {axis_y}C{ROOT_X + 40} {axis_y} {JUNCTION_X - 60} "
        f"{axis_y - 3} {JUNCTION_X} {axis_y}", spec, 0.75, 0.55, 200, 1.4))

    p.append(tl.group(
        f'<circle cx="{ROOT_X}" cy="{axis_y}" r="3.2" fill="{t["paper"]}" '
        f'stroke="{mute}" stroke-width="1.4"/>', 0.95, 0.4))
    p.append(tl.group(
        f'<path d="M{ROOT_X} {axis_y - 9}V{axis_y - 32}" stroke="{line_c}" '
        f'stroke-opacity="{strong_o}" stroke-width="1"/>', 1.0, 0.45))
    p.append(tl.mono(doc.get("upstream", "UPSTREAM"), ROOT_X, axis_y - 42, 11,
                     soft, 1.05, anchor="middle", track=0.5))

    # The junction is where the work leaves, so it takes the accent -- the same
    # role the Kafka bus plays on plate I.
    p.append(tl.group(
        f'<circle cx="{JUNCTION_X}" cy="{axis_y}" r="4.5" fill="{accent}"/>',
        1.15, 0.4))
    p.append(tl.group(
        f'<path d="M{JUNCTION_X} {axis_y + 9}V{axis_y + 34}" stroke="{line_c}" '
        f'stroke-opacity="{strong_o}" stroke-width="1"/>', 1.2, 0.45))
    p.append(tl.mono(f"{merged} MERGED", JUNCTION_X, axis_y + 50, 11, accent,
                     1.3, anchor="middle", track=0.5))

    # --- the grafts --------------------------------------------------------
    for i, c in enumerate(items):
        y = ys[i]
        b = 1.25 + i * 0.16
        cache = c.get("cache", {})

        # S-curve off the junction. `dash` only has to exceed the true arc
        # length, so a generous Manhattan estimate beats measuring the Bezier.
        dy = y - axis_y
        dash = int(NODE_X - JUNCTION_X + abs(dy) * 1.6) + 80
        p.append(tl.draw_on(
            f"M{JUNCTION_X} {axis_y}C{JUNCTION_X + 55} {axis_y} "
            f"{NODE_X - 85} {y} {NODE_X} {y}", spec, b, 0.8, dash, 1.4))

        p.append(tl.group(
            f'<circle cx="{NODE_X}" cy="{y}" r="3.2" fill="{t["paper"]}" '
            f'stroke="{mute}" stroke-width="1.4"/>', b + 0.6, 0.4))

        # meta line: repo · #number ....... state ....... diffstat
        state = cache.get("state", "open")
        is_merged = state == "merged"
        state_c = accent if is_merged else mute

        add, dele = cache.get("additions", 0), cache.get("deletions", 0)
        files = cache.get("changed_files", 0)
        stat = f"{files} files  ·  +{add} / -{dele}" if files else f"+{add} / -{dele}"
        p.append(tl.mono(stat, PAD_R, y + 4, 11, mute, b + 0.8, anchor="end",
                         track=0.2))

        label = state.upper()
        stat_x = PAD_R - measure(stat, "mono", 11, 0.2)
        state_end = stat_x - 26
        state_x = state_end - measure(label, "mono", 10, 0.8)
        p.append(tl.mono(label, state_end, y + 4, 10, state_c, b + 0.78,
                         anchor="end", track=0.8))
        p.append(tl.group(
            f'<circle cx="{state_x - 11}" cy="{y}" r="3" fill="{state_c}"/>',
            b + 0.76, 0.4))

        head = f"{c.get('repo', '')}  #{c.get('pr', '')}"
        p.append(tl.mono(head, TEXT_X, y + 4, 12, soft, b + 0.72, track=0.2))
        p.append(dots(TEXT_X + measure(head, "mono", 12, 0.2) + 12,
                      state_x - 22, y, line_c, strong_o, tl, b + 0.74))

        # title
        title = fit(cache.get("title", ""), "mono", 13, PAD_R - TEXT_X, 0.1)
        p.append(tl.mono(title, TEXT_X, y + TITLE_DY, 13, t["ink"], b + 0.85,
                         track=0.1))

        # tags on the left, merge date on the right
        tags = "  ·  ".join(c.get("tags", []))
        p.append(tl.mono(tags, TEXT_X, y + TAGS_DY, 10, mute, b + 0.95, track=0.5))
        when = cache.get("merged_at")
        if when:
            p.append(tl.mono(when, PAD_R, y + TAGS_DY, 10, mute, b + 0.95,
                             anchor="end", track=0.5))

    p += plate.footer(t, tl, doc.get("figure", "fig. 2"), PAD_L, PAD_R,
                      foot_rule_y, foot_y, foot_begin)
    p.append("</svg>")
    return "".join(x for x in p if x)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    doc = json.loads(DATA.read_text(encoding="utf-8"))
    print(f"  {len(doc.get('contributions', []))} contribution(s)")

    for theme in ("dark", "light"):
        svg = build(theme, doc)
        dest = OUT / f"contributions-{theme}.svg"
        dest.write_text(svg, encoding="utf-8")
        print(f"  wrote {dest.name}  {len(svg) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
