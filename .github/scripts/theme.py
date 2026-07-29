"""Single source of truth for the palette.

Ported from the design tokens on portfolio-tau-tawny-62.vercel.app, with the
"paper" ground shifted from deep navy to deep forest. The warm accent is kept
unchanged: the warm-on-cool tension is the point, so the accent stays ember.

Line colours are kept as (colour, opacity) pairs rather than 8-digit hex so the
output renders identically in strict SVG renderers as well as browsers.
"""

DARK = {
    "paper": "#0B1F17",       # was #0B132B (navy) -> forest
    "paper_deep": "#081611",  # recessed panels
    "ink": "#E2E9E3",         # was #E0E6ED, warmed slightly off-cool
    "ink_soft": "#A8BCAE",    # was #A8B2C1
    "mute": "#6B8A76",        # was #6B7A99
    "specimen": "#A8BCAE",    # branch linework, tuned per theme for equal weight
    "accent": "#FF6B35",      # unchanged
    "line": ("#FFFFFF", 0.08),
    "line_strong": ("#FFFFFF", 0.18),
    "grid": ("#FFFFFF", 0.05),
}

LIGHT = {
    "paper": "#EDE8DF",       # unchanged, the cream reads fine against green
    "paper_deep": "#E4DED3",
    "ink": "#161412",
    "ink_soft": "#3A3631",
    "mute": "#7A736A",
    # Lighter than ink_soft: at #3A3631 the branches read near-black and pull
    # focus off the display type, which dark mode does not do.
    "specimen": "#6E675C",
    "accent": "#C8501E",      # unchanged
    "line": ("#161412", 0.14),
    "line_strong": ("#161412", 0.32),
    "grid": ("#161412", 0.07),
}

THEMES = {"dark": DARK, "light": LIGHT}


def ramp(t: dict, n: int = 4) -> list:
    """Series colours for charts, brightest first.

    Deliberately palette-derived rather than GitHub Linguist's brand colours:
    Linguist's Java orange and TypeScript blue would fight the forest ground and
    undo the point of having a palette at all. Past the third stop the ramp just
    fades mute toward paper, which is enough separation for a legend.
    """
    stops = [t["accent"], t["specimen"], t["mute"]]
    fades = (0.45, 0.62, 0.75, 0.84)
    stops += [mix(t["mute"], t["paper"], f) for f in fades]
    return stops[:max(n, 1)]


def mix(a: str, b: str, t: float) -> str:
    """Blend two hex colours, t=0 -> a, t=1 -> b.

    Used to derive tints that stay inside the palette -- language donut
    segments, for instance, are palette stops faded toward the paper rather
    than Linguist's brand colours, which would fight the forest ground.
    """
    ar, ag, ab = (int(a[i:i + 2], 16) for i in (1, 3, 5))
    br, bg, bb = (int(b[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02X%02X%02X" % (
        round(ar + (br - ar) * t),
        round(ag + (bg - ag) * t),
        round(ab + (bb - ab) * t),
    )

# Motion. cubic-bezier(.2,.8,.2,1) is the portfolio's riseIn curve; SMIL spells
# the same curve as keySplines, so the motion character matches exactly.
EASE = "0.2 0.8 0.2 1"
