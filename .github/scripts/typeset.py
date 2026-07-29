"""Convert text into SVG path outlines using the vendored variable fonts.

Why outlines instead of <text>: SVGs embedded in a GitHub README render in
*image context*, where external resource loading is blocked. A Google Fonts
@import silently fails and everything falls back to the platform default --
which is why essentially every profile SVG on GitHub is monospace and they all
look identical. Outlining the glyphs removes the font dependency entirely, so
Fraunces renders byte-identically in every browser and every renderer.

Trade-off: outlined text is not selectable or searchable. For a banner that is
fine. Generated panels whose text changes (project names, PR titles) use an
embedded base64 subset instead -- see subset.py.
"""

from functools import lru_cache
from pathlib import Path

from fontTools.misc.transform import Transform
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

FONT_DIR = Path(__file__).resolve().parent.parent / "fonts"

FONTS = {
    "fraunces": FONT_DIR / "Fraunces.ttf",
    "fraunces-italic": FONT_DIR / "Fraunces-Italic.ttf",
    "mono": FONT_DIR / "JetBrainsMono.ttf",
}

# Axis defaults per family. Fraunces' opsz is the interesting one: at 144 you
# get the display cut (high contrast, delicate joins), at 9 the text cut. WONK=1
# enables the wonky alternates, which is where the face gets its character.
DEFAULT_AXES = {
    "fraunces": {"opsz": 144, "wght": 600, "SOFT": 0, "WONK": 1},
    "fraunces-italic": {"opsz": 60, "wght": 400, "SOFT": 0, "WONK": 1},
    "mono": {"wght": 400},
}


def _fmt(v: float) -> str:
    """Trim coordinate precision; two decimals is well below one device pixel."""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


@lru_cache(maxsize=None)
def _instance(family: str, axes_key: tuple) -> TTFont:
    """Instantiate a variable font at fixed axis values. Cached: instancing is slow."""
    font = TTFont(FONTS[family])
    return instancer.instantiateVariableFont(font, dict(axes_key), inplace=True)


def _resolve(family: str, axes: dict) -> TTFont:
    merged = dict(DEFAULT_AXES[family])
    merged.update(axes or {})
    return _instance(family, tuple(sorted(merged.items())))


def outline(text, family="fraunces", size=48, x=0, y=0, tracking=0.0, **axes):
    """Render `text` as a single SVG path `d` string.

    `x`/`y` are the start of the baseline. `tracking` is extra letter-spacing in
    user units (applied per glyph, as you would for display type).

    Returns (d, advance_width).
    """
    font = _resolve(family, axes)
    upem = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    glyphset = font.getGlyphSet()
    hmtx = font["hmtx"]
    scale = size / upem

    pen = SVGPathPen(glyphset, ntos=_fmt)
    cursor = float(x)

    for ch in text:
        name = cmap.get(ord(ch))
        if name is None:
            # Missing glyph: advance by a blank and carry on rather than crash.
            cursor += size * 0.5 + tracking
            continue
        # Font coordinates are Y-up, SVG is Y-down, hence the -scale on the y axis.
        glyphset[name].draw(TransformPen(pen, Transform(scale, 0, 0, -scale, cursor, y)))
        cursor += hmtx[name][0] * scale + tracking

    return pen.getCommands(), cursor - x


def measure(text, family="fraunces", size=48, tracking=0.0, **axes) -> float:
    """Advance width of `text` without building the outline."""
    font = _resolve(family, axes)
    scale = size / font["head"].unitsPerEm
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    total = 0.0
    for ch in text:
        name = cmap.get(ord(ch))
        total += (hmtx[name][0] * scale if name else size * 0.5) + tracking
    return total


def fit(text, family="fraunces", size=48, max_w=0, tracking=0.0, **axes) -> str:
    """Truncate `text` with an ellipsis until it fits inside `max_w`.

    Panels render strings that come from the GitHub API -- PR titles, repo
    descriptions -- so every one of them needs a width budget. Trailing spaces
    and punctuation are stripped before the ellipsis so we don't produce
    "guide ,…".
    """
    if measure(text, family, size, tracking, **axes) <= max_w:
        return text
    ell = "…"
    budget = max_w - measure(ell, family, size, tracking, **axes)
    cut = text
    while cut and measure(cut, family, size, tracking, **axes) > budget:
        cut = cut[:-1]
    cut = cut.rstrip(" ,.;:-—·")
    return (cut + ell) if cut else ell


def wrap(text, family="fraunces", size=48, max_w=0, tracking=0.0,
         max_lines=3, **axes) -> list:
    """Greedy word wrap to a measured pixel width.

    The last line is passed through `fit()`, so overflow ends in an ellipsis
    rather than silently disappearing off the edge of a card.
    """
    words, lines, cur, i = text.split(), [], "", 0
    while i < len(words):
        trial = f"{cur} {words[i]}".strip()
        if cur and measure(trial, family, size, tracking, **axes) > max_w:
            lines.append(cur)
            cur = ""
            if len(lines) == max_lines - 1:
                break
            continue
        cur = trial
        i += 1

    # Whatever is left -- the in-progress line plus any words the break skipped
    # -- becomes the final line, ellipsised by fit() if it overflows.
    tail = " ".join(([cur] if cur else []) + words[i:]).strip()
    if tail:
        lines.append(fit(tail, family, size, max_w, tracking, **axes))
    return lines


def path(text, family="fraunces", size=48, x=0, y=0, tracking=0.0,
         fill="#000", opacity=None, anchor="start", extra="", **axes):
    """Full <path> element, with `anchor` handling right/centre alignment.

    Alignment is resolved here by measuring and shifting the origin, because SVG
    has no text-anchor for paths.
    """
    if anchor in ("end", "middle"):
        w = measure(text, family, size, tracking, **axes)
        x = x - w if anchor == "end" else x - w / 2
    d, _ = outline(text, family, size, x, y, tracking, **axes)
    if not d:
        return ""
    op = f' opacity="{opacity}"' if opacity is not None else ""
    sp = f" {extra}" if extra else ""
    return f'<path d="{d}" fill="{fill}"{op}{sp}/>'
