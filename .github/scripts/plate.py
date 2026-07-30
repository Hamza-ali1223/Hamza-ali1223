"""Shared plate chrome and the SMIL timeline helpers.

Every panel on the profile is a plate from the same imaginary field guide: the
same double-rule frame, the same graph-paper ground, the same numbered header
and italic figure caption. This module owns that language so the builders
(`build_banner`, `build_contributions`, `build_projects`, `build_stats`,
`build_contact`) stay purely about their own subject.

THE INVARIANT, which every caller depends on
--------------------------------------------
The *static* attribute on an element holds the SETTLED value, and the animation
holds the start value from t=0 via keyTimes. Two things fall out of that:

 1. Graceful degradation. A renderer that ignores SMIL -- GitHub mobile, feed
    readers, headless screenshotters, some Markdown previewers -- shows the
    finished plate rather than a blank rectangle. Animating the other way
    (opacity="0" rising to 1) means no SMIL, no plate.
 2. No first-frame flash. With `begin="1.5s"` the base value shows until the
    animation starts, so an element would appear, vanish, then fade in. Holding
    the start value from t=0 avoids that.

So: all motion runs over one shared timeline (0..T) and staggers via keyTimes,
never via `begin`. `Timeline` binds the helpers to a T so each panel can pick
its own duration.
"""

from theme import EASE
from typeset import path

SPLINES = f"0 0 1 1;{EASE};0 0 1 1"


def num(v) -> str:
    """Render a number the way it was written: 1.0 -> "1", 0.65 -> "0.65"."""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


class Timeline:
    """SMIL helpers bound to a total duration."""

    def __init__(self, T: float):
        self.T = T

    def _keytimes(self, begin, dur):
        a = min(max(begin / self.T, 0.0), 1.0)
        b = min(max((begin + dur) / self.T, a), 1.0)
        return f"0;{a:.4f};{b:.4f};1"

    def anim(self, attr, frm, to, begin, dur, tag="animate", kind=""):
        """Hold `frm`, ease to `to` between begin and begin+dur, hold `to`."""
        ty = f' type="{kind}"' if kind else ""
        return (
            f'<{tag} attributeName="{attr}"{ty} values="{frm};{frm};{to};{to}" '
            f'keyTimes="{self._keytimes(begin, dur)}" dur="{self.T}s" begin="0s" '
            f'fill="freeze" calcMode="spline" keySplines="{SPLINES}"/>'
        )

    def fade(self, begin, dur=0.6):
        return self.anim("opacity", 0, 1, begin, dur)

    def rise(self, begin, dy=16, dur=1.1):
        """The portfolio's riseIn: translate up into place while fading in."""
        return (
            self.anim("transform", f"0 {dy}", "0 0", begin, dur,
                      tag="animateTransform", kind="translate")
            + self.fade(begin, dur * 0.75)
        )

    def group(self, body, begin, dur=0.6, op=1.0):
        """Wrap `body` in a <g> that fades in. `op` is the settled opacity."""
        return f'<g opacity="{num(op)}">{body}{self.fade(begin, dur)}</g>'

    def draw_on(self, d, stroke, begin, dur, dash, width=1.2, opacity=1.0,
                cap="round"):
        """A stroke that draws itself on.

        `dash` only needs to be >= the true path length: with dasharray N and a
        dashoffset of N the whole path sits in the gap, and walking the offset
        to 0 reveals it. Avoids measuring Bezier arc length at build time.

        Per the invariant, the static stroke-dashoffset is 0 (fully drawn) --
        the animation starts it at `dash` and brings it back.
        """
        return (
            f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{width}" '
            f'stroke-linecap="{cap}" opacity="{opacity}" stroke-dasharray="{dash}" '
            f'stroke-dashoffset="0">'
            + self.anim("stroke-dashoffset", dash, 0, begin, dur)
            + "</path>"
        )

    def rule(self, x1, y, x2, colour, op, begin, dur=0.7, width=1):
        """A horizontal hairline that draws left to right."""
        return self.draw_on(f"M{x1} {y}H{x2}", colour, begin, dur, x2 - x1,
                            width, op, cap="butt")

    def mono(self, text, x, y, size, fill, begin, op=1.0, anchor="start",
             weight=400, track=0.0):
        el = path(text, "mono", size, x, y, track, fill=fill, anchor=anchor,
                  wght=weight)
        return self.group(el, begin, op=op) if el else ""


# --- plate chrome -----------------------------------------------------------

def open_svg(w, h, title, desc, aria):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" role="img" aria-label="{aria}">'
        f"<title>{title}</title><desc>{desc}</desc>"
    )


def ground(t, tl, uid, w, h):
    """Paper, graph-paper grid, and the double-rule frame.

    The frame insets are fixed at 20 and 27 regardless of panel size, so the
    plates all read as the same object at different heights. Dash lengths are
    the exact rectangle perimeters.
    """
    grid_c, grid_o = t["grid"]
    line_c, line_o = t["line"]
    strong_c, strong_o = t["line_strong"]

    ow, oh = w - 40, h - 40   # outer frame
    iw, ih = w - 54, h - 54   # inner frame, also the grid's extent

    return [
        f'<defs><pattern id="grid-{uid}" width="40" height="40" '
        f'patternUnits="userSpaceOnUse">'
        f'<path d="M40 0H0V40" fill="none" stroke="{grid_c}" '
        f'stroke-opacity="{grid_o}" stroke-width="1"/></pattern></defs>',

        f'<rect width="{w}" height="{h}" fill="{t["paper"]}"/>',

        tl.group(f'<rect x="27" y="27" width="{iw}" height="{ih}" '
                 f'fill="url(#grid-{uid})"/>', 0.1, 1.0),

        f'<rect x="20" y="20" width="{ow}" height="{oh}" fill="none" '
        f'stroke="{strong_c}" stroke-opacity="{strong_o}" stroke-width="1.2" '
        f'stroke-dasharray="{2 * (ow + oh)}" stroke-dashoffset="0">'
        + tl.anim("stroke-dashoffset", 2 * (ow + oh), 0, 0.05, 1.0)
        + "</rect>",

        f'<rect x="27" y="27" width="{iw}" height="{ih}" fill="none" '
        f'stroke="{line_c}" stroke-opacity="{line_o}" stroke-width="1" '
        f'stroke-dasharray="{2 * (iw + ih)}" stroke-dashoffset="0">'
        + tl.anim("stroke-dashoffset", 2 * (iw + ih), 0, 0.15, 1.0)
        + "</rect>",
    ]


def header(t, tl, left, right, pad_l, pad_r, y=72, rule_y=92, begin=0.5):
    """Section number on the left, plate identity on the right, rule under."""
    line_c, line_o = t["line"]
    mute = t["mute"]
    return [
        tl.mono(left, pad_l, y, 13, mute, begin + 0.1, track=0.6),
        tl.mono(right, pad_r, y, 13, mute, begin + 0.18, anchor="end", track=0.6),
        tl.rule(pad_l, rule_y, pad_r, line_c, line_o, begin),
    ]


def footer(t, tl, caption, pad_l, pad_r, rule_y, y, begin=2.0):
    """Closing rule and the italic figure caption.

    17px rather than the 15 this was in Fraunces: Newsreader's x-height is
    0.426em against Fraunces' 0.482em, so the same nominal size would have read
    noticeably smaller on the one line of type every plate shares.
    """
    line_c, line_o = t["line"]
    el = path(caption, "newsreader-italic", 17, pad_l, y,
              fill=t["mute"], opsz=14, wght=400)
    return [
        tl.rule(pad_l, rule_y, pad_r, line_c, line_o, begin, 0.8),
        tl.group(el, begin + 0.15, 0.7),
    ]
