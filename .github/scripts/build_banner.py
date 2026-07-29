"""Build assets/banner-dark.svg and banner-light.svg.

Concept: a botanical specimen plate whose specimen is a service topology. The
plate supplies the presentation language (double-rule frame, section numbering,
aligned annotation labels with leader lines, italic figure caption); the branch
diagram supplies the subject -- the real PulseTrack topology, drawn as if from
life.

All motion is SMIL. Line work arrives by animating stroke-dashoffset so the
structure draws itself on; type arrives with a translate+opacity rise. The
easing is the portfolio's own cubic-bezier(.2,.8,.2,1), expressed as keySplines.

The plate chrome and the timeline helpers live in plate.py, shared with the
contributions and projects panels.
"""

from pathlib import Path

import plate
from plate import Timeline
from theme import THEMES
from typeset import measure, path

W, H = 1200, 380
OUT = Path(__file__).resolve().parent.parent.parent / "assets"

# --- layout -----------------------------------------------------------------
PAD_L, PAD_R = 56, 1144
HEAD_Y, HEAD_RULE_Y = 72, 92
FOOT_RULE_Y, FOOT_Y = 314, 340

TRUNK_X, AXIS_Y = 95, 205
JUNCTION_X = 215
LABEL_X, LEADER_X = 452, 444

CAP_X = 648
NAME_Y, NAME_SIZE = 182, 72
CAP_RULE_Y = 202
ROLE_Y, STACK_Y, STATUS_Y = 230, 256, 290

# Branch tips, drawn from the real PulseTrack service topology.
BRANCHES = [
    ("BILLING",   "M215 205C262 205 272 152 318 139C348 131 378 130 405 129", 405, 129, 300),
    ("ANALYTICS", "M215 205C255 205 264 181 302 173C332 167 358 166 385 165", 385, 165, 260),
    ("NOTIFY",    "M215 205C255 205 264 229 302 237C332 243 358 244 385 245", 385, 245, 260),
    ("AUTH",      "M215 205C262 205 272 258 318 271C348 279 378 280 405 281", 405, 281, 300),
]

TRUNK = "M95 205C130 205 172 203 215 205"

STACK = "Java  ·  Spring Boot  ·  Kafka  ·  Docker  ·  GenAI"
CAPTION = "fig. 1 — a distributed system, drawn from life"

tl = Timeline(3.4)


def build(name: str) -> str:
    t = THEMES[name]
    line_c, _ = t["line"]
    strong_c, strong_o = t["line_strong"]
    ink, soft, mute, accent = t["ink"], t["ink_soft"], t["mute"], t["accent"]
    spec = t["specimen"]
    uid = name[0]

    p = [plate.open_svg(
        W, H,
        "Hamza Ali — Backend Architect · Systems Thinker",
        "A botanical specimen plate in which the specimen is a distributed "
        "system: a branching diagram labelled with the services of the PulseTrack "
        "backend.",
        "Hamza Ali — Backend Architect and Systems Thinker",
    )]
    p += plate.ground(t, tl, uid, W, H)
    p += plate.header(t, tl, "§ 00", "PLATE I  ·  SPECIMEN", PAD_L, PAD_R,
                      HEAD_Y, HEAD_RULE_Y)

    # --- specimen ----------------------------------------------------------
    p.append(tl.draw_on(TRUNK, spec, 0.75, 0.55, 160, 1.4))

    for i, (label, d, tx, ty, dash) in enumerate(BRANCHES):
        b = 1.05 + i * 0.13
        p.append(tl.draw_on(d, spec, b, 0.8, dash, 1.4))
        # Tip node, then leader, then label -- each waiting on the one before.
        p.append(tl.group(
            f'<circle cx="{tx}" cy="{ty}" r="3.2" fill="{t["paper"]}" '
            f'stroke="{mute}" stroke-width="1.4"/>', b + 0.7, 0.4))
        p.append(tl.rule(tx + 7, ty, LEADER_X, line_c, strong_o, b + 0.85, 0.45))
        p.append(tl.mono(label, LABEL_X, ty + 3.8, 11, soft, b + 0.95, track=0.5))

    # Junction: the bus everything hangs off, so it gets the accent.
    p.append(tl.group(
        f'<circle cx="{JUNCTION_X}" cy="{AXIS_Y}" r="4.5" fill="{accent}"/>',
        1.15, 0.4))
    p.append(tl.group(
        f'<path d="M{JUNCTION_X} {AXIS_Y + 9}V{AXIS_Y + 36}" stroke="{line_c}" '
        f'stroke-opacity="{strong_o}" stroke-width="1"/>', 1.9, 0.45))
    p.append(tl.mono("KAFKA BUS", JUNCTION_X, AXIS_Y + 52, 11, accent, 2.0,
                     anchor="middle", track=0.5))

    # Source node.
    p.append(tl.group(
        f'<circle cx="{TRUNK_X}" cy="{AXIS_Y}" r="3.2" fill="{t["paper"]}" '
        f'stroke="{mute}" stroke-width="1.4"/>', 0.95, 0.4))
    p.append(tl.group(
        f'<path d="M{TRUNK_X} {AXIS_Y - 9}V{AXIS_Y - 32}" stroke="{line_c}" '
        f'stroke-opacity="{strong_o}" stroke-width="1"/>', 1.05, 0.45))
    p.append(tl.mono("PATIENT", TRUNK_X, AXIS_Y - 42, 11, soft, 1.15,
                     anchor="middle", track=0.5))

    # --- caption block -----------------------------------------------------
    name_el = path("Hamza Ali", "fraunces", NAME_SIZE, CAP_X, NAME_Y,
                   fill=ink, opsz=144, wght=600, WONK=1)
    p.append(f'<g opacity="1">{name_el}{tl.rise(1.0, 16, 1.2)}</g>')

    p.append(tl.rule(CAP_X, CAP_RULE_Y, CAP_X + 300, strong_c, strong_o, 1.5, 0.8))
    p.append(tl.mono("Backend Architect  ·  Systems Thinker", CAP_X, ROLE_Y, 14,
                     soft, 1.55, track=0.2))
    p.append(tl.mono(STACK, CAP_X, STACK_Y, 12, mute, 1.7, track=0.2))

    # Status dot -- the one thing that keeps moving after everything settles.
    p.append(tl.group(
        f'<circle cx="{CAP_X + 5}" cy="{STATUS_Y - 4}" r="4" fill="{accent}"/>'
        f'<circle cx="{CAP_X + 5}" cy="{STATUS_Y - 4}" r="4" fill="none" '
        f'stroke="{accent}" stroke-width="1.4">'
        f'<animate attributeName="r" values="4;12" begin="2.4s" dur="2s" '
        f'repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="0.65;0" begin="2.4s" dur="2s" '
        f'repeatCount="indefinite"/></circle>', 1.85, 0.5))
    p.append(tl.mono("JAMSHORO, PK", CAP_X + 20, STATUS_Y, 11, mute, 1.9, track=0.6))

    p += plate.footer(t, tl, CAPTION, PAD_L, PAD_R, FOOT_RULE_Y, FOOT_Y)
    p.append("</svg>")
    return "".join(x for x in p if x)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    name_w = measure("Hamza Ali", "fraunces", NAME_SIZE, opsz=144, wght=600, WONK=1)
    print(f'  name "Hamza Ali" -> {name_w:.1f}px wide '
          f"(budget {PAD_R - CAP_X}px, ends x={CAP_X + name_w:.0f})")
    print(f'  caption -> {measure(CAPTION, "fraunces-italic", 15, opsz=60):.1f}px')
    print(f'  stack   -> {measure(STACK, "mono", 12, 0.2):.1f}px')

    for theme in ("dark", "light"):
        svg = build(theme)
        dest = OUT / f"banner-{theme}.svg"
        dest.write_text(svg, encoding="utf-8")
        print(f"  wrote {dest.name}  {len(svg) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
