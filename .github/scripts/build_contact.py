"""Build assets/contact-dark.svg and contact-light.svg.

This plate replaces what section 06 used to be: two img.shields.io badges and a
visitor-badge.laobi.icu counter. They were the last third-party images on the
page, which made them the same bug plate IV was written to fix -- a section that
goes blank when somebody else's free tier does. They also hardcoded
`color=0B1F17`, the dark-mode forest, so in light mode section 06 was the one
block on the page that did not flip with the reader's theme.

Why the plate carries no links. GitHub proxies README SVGs through camo and
renders them as <img>, and an <a> inside an image never resolves -- so four
clickable rows are not available at any price. The division of labour that
follows: the plate carries the design and says what to write about, and a plain
Markdown link row underneath carries the clicks. Anything added here must keep
working as a picture.

Reads contact.json, which is hand-written -- there is no cache block and
fetch_data.py never touches it.
"""

import json
from pathlib import Path

import plate
from plate import Timeline
from theme import THEMES
from typeset import fit, measure, path, wrap

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "assets"
DATA = ROOT / "contact.json"

W, H = 1200, 300

# --- layout -----------------------------------------------------------------
PAD_L, PAD_R = 56, 1144
HEAD_Y, HEAD_RULE_Y = 72, 92
FOOT_RULE_Y, FOOT_Y = 234, 260

DIVIDER_X = 608

# Left: the invitation, then where I am. Three wrapped lines plus the location
# is what fits between the two rules; the leading is tight for display type
# because the alternative is the location sitting on the closing rule.
NOTE_SIZE, NOTE_MAX_W = 26, 520
NOTE_Y, NOTE_LEAD = 126, 31
LOC_DY = 26                      # under the last line of the invitation

# Right: label ...... value, four rows, bottoming out level with the location.
CHAN_X = 648
ROW_Y, ROW_LEAD = 140, 25
LABEL_SIZE, VALUE_SIZE = 10, 13
LEADER_GAP = 12                  # air either side of the dotted leader
LEADER_MIN = 24                  # a leader shorter than this reads as a typo


def dots(x1, x2, y, colour, op, tl, begin):
    """A dotted leader, as on plate II.

    Faded in rather than drawn on for the reason given there: draw_on works by
    animating stroke-dashoffset against a stroke-dasharray, and this line needs
    its dasharray for the dots themselves.
    """
    if x2 - x1 < 12:
        return ""
    return tl.group(
        f'<path d="M{x1:.1f} {y}H{x2:.1f}" stroke="{colour}" '
        f'stroke-opacity="{op}" stroke-width="1" stroke-dasharray="1 5" '
        f'stroke-linecap="round"/>',
        begin, 0.5)


def value_budget(label):
    """How much width a row's value has left once its label and leader are in."""
    label_w = measure(label, "mono", LABEL_SIZE, 0.6)
    return PAD_R - (CHAN_X + label_w + LEADER_GAP * 2 + LEADER_MIN)


def note_lines(text):
    """The invitation, wrapped to the left column."""
    return wrap(text, "fraunces", NOTE_SIZE, NOTE_MAX_W, 0.0, max_lines=3,
                opsz=144, wght=600, WONK=1)


def build(name, doc):
    t = THEMES[name]
    line_c, line_o = t["line"]
    _, strong_o = t["line_strong"]
    ink, soft, mute = t["ink"], t["ink_soft"], t["mute"]
    # "c" is already plate II's; correspondence takes k.
    uid = "k" + name[0]

    channels = doc.get("channels", [])
    tl = Timeline(3.2)

    p = [plate.open_svg(
        W, H,
        "Correspondence — Hamza Ali",
        "A plate giving the ways to reach Hamza Ali: email, LinkedIn, "
        "portfolio and GitHub, alongside a note on what to write about.",
        "Contact details for Hamza Ali: "
        + ", ".join(c.get("label", "").title() for c in channels),
    )]
    p += plate.ground(t, tl, uid, W, H)
    p += plate.header(t, tl, "§ 06", "PLATE V  ·  CORRESPONDENCE", PAD_L, PAD_R,
                      HEAD_Y, HEAD_RULE_Y)

    # --- the invitation ----------------------------------------------------
    # The one piece of display type on the plate, so it takes the same Fraunces
    # cut the project names do rather than inventing a third.
    lines = note_lines(doc.get("open_to", ""))
    for i, ln in enumerate(lines):
        p.append(tl.group(
            path(ln, "fraunces", NOTE_SIZE, PAD_L, NOTE_Y + i * NOTE_LEAD,
                 fill=ink, opsz=144, wght=600, WONK=1),
            0.75 + i * 0.09, 0.6))

    loc_y = NOTE_Y + (len(lines) - 1) * NOTE_LEAD + LOC_DY
    p.append(tl.mono(doc.get("location", ""), PAD_L, loc_y, 11, mute, 1.05,
                     track=0.6))

    # Divider between the invitation and the addresses.
    p.append(tl.draw_on(f"M{DIVIDER_X} 118V220", line_c, 0.6, 0.9, 102, 1,
                        strong_o, cap="butt"))

    # --- the addresses -----------------------------------------------------
    for i, c in enumerate(channels):
        y = ROW_Y + i * ROW_LEAD
        b = 1.15 + i * 0.14

        label = c.get("label", "")
        p.append(tl.mono(label, CHAN_X, y, LABEL_SIZE, mute, b, track=0.6))

        value = fit(c.get("value", ""), "mono", VALUE_SIZE,
                    value_budget(label), 0.2)
        p.append(tl.mono(value, PAD_R, y, VALUE_SIZE, soft, b + 0.1,
                         anchor="end", track=0.2))

        # Leader between the two, sitting on the x-height rather than the
        # baseline so it reads as a rule and not an underline.
        x1 = CHAN_X + measure(label, "mono", LABEL_SIZE, 0.6) + LEADER_GAP
        x2 = PAD_R - measure(value, "mono", VALUE_SIZE, 0.2) - LEADER_GAP
        p.append(dots(x1, x2, y - 4, line_c, strong_o, tl, b + 0.06))

    p += plate.footer(t, tl, doc.get("figure", "fig. 5"), PAD_L, PAD_R,
                      FOOT_RULE_Y, FOOT_Y, 2.2)
    p.append("</svg>")
    return "".join(x for x in p if x)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    doc = json.loads(DATA.read_text(encoding="utf-8"))
    channels = doc.get("channels", [])
    print(f"  {len(channels)} channel(s)")

    lines = note_lines(doc.get("open_to", ""))
    widest = max((measure(ln, "fraunces", NOTE_SIZE, opsz=144, wght=600, WONK=1)
                  for ln in lines), default=0)
    print(f"  invitation -> {len(lines)} line(s), widest {widest:.0f}px "
          f"(column is {NOTE_MAX_W}px)")

    loc_y = NOTE_Y + (len(lines) - 1) * NOTE_LEAD + LOC_DY
    print(f"  location   -> baseline y={loc_y} (foot rule is {FOOT_RULE_Y})")

    for c in channels:
        label, value = c.get("label", ""), c.get("value", "")
        w = measure(value, "mono", VALUE_SIZE, 0.2)
        print(f"  {label:<10} -> value {w:.0f}px (budget {value_budget(label):.0f}px)")

    last_row_y = ROW_Y + (max(len(channels), 1) - 1) * ROW_LEAD
    print(f"  last row   -> baseline y={last_row_y} (foot rule is {FOOT_RULE_Y})")

    for theme in ("dark", "light"):
        svg = build(theme, doc)
        dest = OUT / f"contact-{theme}.svg"
        dest.write_text(svg, encoding="utf-8")
        print(f"  wrote {dest.name}  {len(svg) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
