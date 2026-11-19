#!/usr/bin/env python3
"""Generate meme.png for gta6-meme-x-01 — deterministic, stdlib only.

Joke: 13 years waiting for GTA 6. Meanwhile the make.fun ghost already
got paid. Vice City sunset beach, palm tree, the white ghost holding its
magenta star coin, and a make.fun band at the bottom.

Deterministic: same input -> same PNG bytes (fixed palette, fixed
geometry, zlib level fixed, no timestamps in the PNG).
"""

import struct
import zlib

W, H = 960, 960

# ---------------------------------------------------------------- palette
PURPLE = (45, 27, 78)
MAGENTA = (214, 0, 110)
ORANGE = (255, 140, 66)
SUN = (255, 236, 170)
OCEAN = (23, 140, 160)
OCEAN_DARK = (16, 110, 130)
SAND = (240, 193, 132)
SAND_DARK = (222, 170, 105)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
YELLOW = (255, 224, 102)
TRUNK = (139, 90, 43)
LEAF = (34, 139, 87)
COIN = (230, 0, 126)
BAND = (200, 0, 100)

# ------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 cells, '#' = on.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '3': ("11111", "00010", "00010", "01110", "00001", "00001", "11110"),
    '6': ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    'a': ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    'e': ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    'f': ("00110", "01000", "01000", "11110", "01000", "01000", "01000"),
    'k': ("00000", "10000", "10010", "10100", "11000", "10100", "10010"),
    'm': ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    'n': ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    'u': ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    '+': ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


def text_width(text, scale):
    return len(text) * (5 * scale + scale) - scale


def draw_text(px, text, x, y, scale, color, outline=None):
    """Draw text at (x, y) top-left; outline drawn first, 1 cell thick."""
    if outline is not None:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1),
                       (-1, -1), (1, -1), (-1, 1), (1, 1)):
            draw_text(px, text, x + dx * scale, y + dy * scale,
                      scale, outline, None)
    cx = x
    for ch in text:
        glyph = FONT[ch]
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == '1':
                    px.fill_rect(cx + col * scale, y + row * scale,
                                 scale, scale, color)
        cx += 6 * scale


def draw_text_centered(px, text, y, scale, color, outline=None):
    draw_text(px, text, (W - text_width(text, scale)) // 2,
              y, scale, color, outline)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = color

    def fill_rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i], self.buf[i + 1], self.buf[i + 2] = color

    def fill_circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            dx = int((r * r - dy * dy) ** 0.5) if r * r >= dy * dy else -1
            if dx >= 0:
                self.fill_rect(cx - dx, yy, 2 * dx + 1, 1, color)

    def thick_line(self, x0, y0, x1, y1, width, color):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1) * 2
        for s in range(steps + 1):
            t = s / steps
            x = int(x0 + (x1 - x0) * t)
            y = int(y0 + (y1 - y0) * t)
            self.fill_circle(x, y, width // 2, color)

    def fill_polygon(self, points, color):
        """Scanline fill for a simple polygon."""
        ys = [p[1] for p in points]
        for y in range(max(0, min(ys)), min(self.h, max(ys)) + 1):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[j]), y,
                               max(1, int(xs[j + 1]) - int(xs[j])), 1, color)


def lerp(c0, c1, t):
    return tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))


def star_points(cx, cy, r_outer, r_inner, points, rot=-90):
    import math
    out = []
    for i in range(points * 2):
        r = r_outer if i % 2 == 0 else r_inner
        a = math.radians(rot + i * 180 / points)
        out.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
    return out


def sparkle_points(cx, cy, r):
    w = max(2, r // 4)
    return [(cx, cy - r), (cx + w, cy - w), (cx + r, cy), (cx + w, cy + w),
            (cx, cy + r), (cx - w, cy + w), (cx - r, cy), (cx - w, cy - w)]


# --------------------------------------------------------------- the scene
def draw_ghost(px, cx, top, width):
    """make.fun ghost: white body, thick black outline, sparkle eyes,
    one round hand holding a magenta coin with a white star."""
    r = width // 2
    mid_y = top + r
    bottom = top + int(width * 1.15)
    # black silhouette (outline), then white body inset by 7 px
    for inset, color in ((0, BLACK), (7, WHITE)):
        rr = r - inset
        px.fill_circle(cx, mid_y, rr, color)
        px.fill_rect(cx - rr, mid_y, 2 * rr, bottom - mid_y - 20, color)
        for bx in (cx - rr + 42, cx, cx + rr - 42):
            px.fill_circle(bx, bottom - 20, 42 - inset, color)
    # sparkle eyes
    for ex in (cx - 52, cx + 52):
        px.fill_polygon(sparkle_points(ex, mid_y - 18, 30), BLACK)
    # little round hand on the right, holding the coin
    px.fill_circle(cx + r + 8, mid_y + 118, 26, BLACK)
    px.fill_circle(cx + r + 8, mid_y + 118, 19, WHITE)
    # magenta coin with white star
    coin_cx, coin_cy, coin_r = cx + r + 62, mid_y + 78, 54
    px.fill_circle(coin_cx, coin_cy, coin_r, BLACK)
    px.fill_circle(coin_cx, coin_cy, coin_r - 6, COIN)
    px.fill_polygon(star_points(coin_cx, coin_cy, 34, 14, 5), WHITE)


def draw_palm(px):
    # trunk: gentle curve from the sand up to the left
    pts = [(120, 730), (128, 640), (142, 560), (162, 490), (178, 430)]
    for a, b in zip(pts, pts[1:]):
        px.thick_line(a[0], a[1], b[0], b[1], 26, TRUNK)
    top = pts[-1]
    # fronds drooping from the crown
    for tip in [(55, 480), (110, 520), (180, 540), (250, 520),
                (305, 480), (270, 560), (90, 560)]:
        mx = (top[0] + tip[0]) // 2
        my = min(top[1], tip[1]) - 34
        px.thick_line(top[0], top[1], mx, my, 12, LEAF)
        px.thick_line(mx, my, tip[0], tip[1], 12, LEAF)
    px.fill_circle(top[0], top[1], 14, TRUNK)


def draw_scene():
    px = Canvas(W, H)
    # sky: purple -> magenta -> orange
    for y in range(0, 600):
        if y < 300:
            c = lerp(PURPLE, MAGENTA, y / 300)
        else:
            c = lerp(MAGENTA, ORANGE, (y - 300) / 300)
        px.fill_rect(0, y, W, 1, c)
    # sun with a soft halo
    px.fill_circle(730, 320, 130, (255, 200, 120))
    px.fill_circle(730, 320, 105, SUN)
    # two birds in the empty sky on the left
    for bx, by in ((250, 250), (340, 215)):
        px.thick_line(bx - 18, by, bx, by - 10, 6, BLACK)
        px.thick_line(bx, by - 10, bx + 18, by, 6, BLACK)
    # ocean + waves
    px.fill_rect(0, 600, W, 120, OCEAN)
    px.fill_rect(0, 600, W, 6, OCEAN_DARK)
    for wy, wx0, wl in ((632, 80, 200), (632, 560, 260), (668, 300, 300),
                         (668, 700, 180), (700, 120, 240), (700, 520, 300)):
        px.fill_rect(wx0, wy, wl, 5, WHITE)
    # sand
    px.fill_rect(0, 720, W, 240, SAND)
    for sx, sy in ((60, 800), (880, 780), (840, 830), (120, 850), (760, 700)):
        px.fill_circle(sx, sy, 4, SAND_DARK)

    draw_palm(px)
    draw_ghost(px, 520, 330, 280)

    # headline
    draw_text_centered(px, "13 YEARS WAITING", 48, 8, WHITE, BLACK)
    draw_text_centered(px, "FOR GTA 6", 132, 8, YELLOW, BLACK)
    # punchline on the sand, clear of the waves
    draw_text_centered(px, "MEANWHILE THE GHOST GOT PAID", 740, 5, WHITE, BLACK)
    # make.fun band
    px.fill_rect(0, 850, W, 110, BAND)
    draw_text_centered(px, "make.fun", 866, 8, WHITE)
    draw_text_centered(px, "REAL MONEY FOR HUMANS AND AGENTS", 924, 4, WHITE)
    return px


# --------------------------------------------------------------- PNG out
def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(px, path):
    raw = bytearray()
    for y in range(px.h):
        raw.append(0)  # filter: none
        raw.extend(px.buf[y * px.w * 3:(y + 1) * px.w * 3])
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", px.w, px.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


if __name__ == "__main__":
    write_png(draw_scene(), "meme.png")
    print("wrote meme.png")
