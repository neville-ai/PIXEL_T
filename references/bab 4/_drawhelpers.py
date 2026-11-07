"""Shared box-drawing helpers for PIXEL-T diagram rendering (UML-standard,
monochrome, minimal). Produces PIL RGB images at 2x scale from a simple
declarative layout."""
from __future__ import annotations

import math
from PIL import Image, ImageDraw, ImageFont

SCALE = 2

# Default Windows fonts with fallbacks.
FONT_REG = "C:/Windows/Fonts/segoeui.ttf"
FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_ITALIC = "C:/Windows/Fonts/segoeuii.ttf"


def _font(size: int, bold: bool = False, italic: bool = False) -> ImageFont.FreeTypeFont:
    try:
        path = FONT_BOLD if bold else (FONT_ITALIC if italic else FONT_REG)
        return ImageFont.truetype(path, max(6, int(size * SCALE)))
    except Exception:
        return ImageFont.load_default()


def text_w(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    return max(1, int((r - l) / SCALE))


def new_img(w: int, h: int):
    img = Image.new("RGB", (w * SCALE, h * SCALE), "white")
    return img, ImageDraw.Draw(img)


def save(img: Image.Image, path: str):
    img.save(path)


def rect(draw: ImageDraw.ImageDraw, x: float, y: float, w: float, h: float,
         fill: str = "white", outline: str = "black", lw: float = 1.0,
         dash: bool = False):
    """Draw a rounded-free rectangle."""
    if dash:
        # dashed outline approximation: draw sides as dash segments
        for xx in [x, x + w]:
            yy = y
            while yy < y + h:
                seg = min(8 * SCALE, (y + h) - yy)
                draw.line([(xx * SCALE, yy * SCALE), (xx * SCALE, (yy + seg) * SCALE)],
                          fill=outline, width=max(1, int(lw * SCALE)))
                yy += seg + 4 * SCALE
        for yy in [y, y + h]:
            xx = x
            while xx < x + w:
                seg = min(8 * SCALE, (x + w) - xx)
                draw.line([(xx * SCALE, yy * SCALE), ((xx + seg) * SCALE, yy * SCALE)],
                          fill=outline, width=max(1, int(lw * SCALE)))
                xx += seg + 4 * SCALE
    else:
        draw.rectangle([x * SCALE, y * SCALE, (x + w) * SCALE, (y + h) * SCALE],
                       fill=fill, outline=outline, width=max(1, int(lw * SCALE)))


def text(draw: ImageDraw.ImageDraw, x: float, y: float, s: str,
         font: ImageFont.FreeTypeFont | None = None, fill: str = "black",
         center: bool = False, anchor: str = "lt"):
    if font is None:
        font = _font(9)
    lines = s.split("\n")
    # text_w supports single line; for center with multiline use widest line.
    if center:
        w = max(text_w(draw, ln, font) for ln in lines)
        x = x - w / 2
    yy = y
    for ln in lines:
        draw.text((x * SCALE, yy * SCALE), ln, font=font, fill=fill, anchor=anchor)
        yy += 11


def box(draw: ImageDraw.ImageDraw, x: float, y: float, w: float, h: float,
        title: str, lines: list[str] | None = None,
        title_font=None, line_font=None, fill: str = "white",
        lw: float = 1.0) -> tuple[float, float]:
    """Standard UML-style class/actor box: title underlined, then attribute lines."""
    rect(draw, x, y, w, h, fill=fill, lw=lw)
    tf = title_font or _font(10, bold=True)
    text(draw, x + 5, y + 4, title, font=tf, center=False)
    yy = y + 4 + 14 + 2
    draw.line([(x * SCALE, yy * SCALE), ((x + w) * SCALE, yy * SCALE)],
              fill="black", width=max(1, int(lw * SCALE)))
    yy += 4
    bf = line_font or _font(9)
    if lines:
        for ln in lines:
            text(draw, x + 5, yy, ln, font=bf)
            yy += 12
    return (x, y, w, h)


def arrow(draw: ImageDraw.ImageDraw, x0: float, y0: float, x1: float, y1: float,
          lw: float = 1.0, dashed: bool = False, head: str = "open",
          color: str = "black"):
    """Draw a line with an arrowhead pointing at (x1,y1)."""
    dx = x1 - x0
    dy = y1 - y0
    dist = math.hypot(dx, dy)
    if dist < 1:
        return
    ux, uy = dx / dist, dy / dist
    if dashed:
        seg = 7 * SCALE
        gap = 4 * SCALE
        step = seg + gap
        covered = 0.0
        while covered < dist:
            end = min(dist, covered + seg)
            draw.line([((x0 + ux * covered) * SCALE, (y0 + uy * covered) * SCALE),
                       ((x0 + ux * end) * SCALE, (y0 + uy * end) * SCALE)],
                      fill=color, width=max(1, int(lw * SCALE)))
            covered = end + gap
    else:
        draw.line([(x0 * SCALE, y0 * SCALE), (x1 * SCALE, y1 * SCALE)],
                  fill=color, width=max(1, int(lw * SCALE)))

    # arrowhead
    ah = 9 * SCALE
    aw = 6 * SCALE
    if head == "open":
        # <- open arrowhead (backward from tip along -ux)
        back = (x1 - ux * 11 * SCALE, y1 - uy * 11 * SCALE)
        draw.line([(x1 * SCALE, y1 * SCALE),
                   ((x1 - ux * ah - uy * aw) * SCALE, (y1 - uy * ah + ux * aw) * SCALE)],
                  fill=color, width=max(1, int(lw * SCALE)))
        draw.line([(x1 * SCALE, y1 * SCALE),
                   ((x1 - ux * ah + uy * aw) * SCALE, (y1 - uy * ah - ux * aw) * SCALE)],
                  fill=color, width=max(1, int(lw * SCALE)))
    elif head == "fill":
        draw.polygon([
            (x1 * SCALE, y1 * SCALE),
            ((x1 - ux * ah + uy * aw) * SCALE, (y1 - uy * ah - ux * aw) * SCALE),
            ((x1 - ux * ah - uy * aw) * SCALE, (y1 - uy * ah + ux * aw) * SCALE),
        ], fill=color)


def actor(draw: ImageDraw.ImageDraw, cx: float, cy: float, label: str,
         r: float = 14, line_font=None):
    """Standard UML stick-figure actor."""
    bf = line_font or _font(9, bold=True)
    # head
    draw.ellipse([(cx - r) * SCALE, (cy - r) * SCALE, (cx + r) * SCALE, (cy + r) * SCALE],
                 outline="black", width=max(1, int(1.5 * SCALE)))
    # body
    draw.line([(cx * SCALE, (cy + r) * SCALE), (cx * SCALE, (cy + r + 26) * SCALE)],
              fill="black", width=max(1, int(1.5 * SCALE)))
    # arms
    draw.line([(cx - 18) * SCALE, (cy + r + 10) * SCALE, (cx + 18) * SCALE, (cy + r + 10) * SCALE],
              fill="black", width=max(1, int(1.5 * SCALE)))
    # legs
    draw.line([(cx * SCALE, (cy + r + 26) * SCALE), ((cx - 14) * SCALE, (cy + r + 46) * SCALE)],
              fill="black", width=max(1, int(1.5 * SCALE)))
    draw.line([(cx * SCALE, (cy + r + 26) * SCALE), ((cx + 14) * SCALE, (cy + r + 46) * SCALE)],
              fill="black", width=max(1, int(1.5 * SCALE)))
    # label below legs
    w = text_w(draw, label, bf)
    text(draw, cx - w / 2, cy + r + 50, label, font=bf)
