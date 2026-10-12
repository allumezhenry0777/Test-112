"""Render a 5-second cartoon clip: a white terrier at the dining table
happily eating Greek yogurt and salad.

Usage: python3 scripts/make_terrier_video.py [output.mp4]
Requires Pillow, NumPy and an ffmpeg binary on PATH.
"""
import math
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter

W, H = 1280, 720
S = 2  # supersampling factor
FPS = 30
DURATION = 5.0
FRAMES = int(FPS * DURATION)

FUR = (251, 250, 246, 255)
FUR_SHADE = (214, 212, 206, 255)
FUR_MID = (238, 236, 230, 255)
BLACK = (28, 24, 26, 255)
PINK = (242, 140, 160, 255)
DARK_PINK = (196, 82, 104, 255)


def s(v):
    return int(round(v * S))


def ell(d, cx, cy, rx, ry, fill, outline=None, width=0):
    d.ellipse([s(cx - rx), s(cy - ry), s(cx + rx), s(cy + ry)],
              fill=fill, outline=outline, width=s(width) if width else 0)


def poly(d, pts, fill, outline=None, width=0):
    d.polygon([(s(x), s(y)) for x, y in pts], fill=fill, outline=outline,
              width=s(width) if width else 0)


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def window(t, a, b):
    return a <= t < b


def interp_keys(keys, t):
    if t <= keys[0][0]:
        return keys[0][1:]
    for k0, k1 in zip(keys, keys[1:]):
        if k0[0] <= t <= k1[0]:
            u = smooth((t - k0[0]) / (k1[0] - k0[0]))
            return tuple(a + (b - a) * u for a, b in zip(k0[1:], k1[1:]))
    return keys[-1][1:]


def fluffy(d, circles, pad=3.5):
    """Draw a fluffy silhouette from (cx, cy, r) circles with a soft outline."""
    for cx, cy, r in circles:
        ell(d, cx, cy, r + pad, r + pad, FUR_SHADE)
    for cx, cy, r in circles:
        ell(d, cx, cy, r, r, FUR)


# ---------------------------------------------------------------- background
def build_background():
    img = Image.new("RGBA", (s(W), s(H)), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    # Warm wall with soft stripes
    for y in range(0, s(H)):
        k = y / s(H)
        c = (int(250 - 18 * k), int(236 - 22 * k), int(208 - 26 * k), 255)
        d.line([(0, y), (s(W), y)], fill=c)
    for x in range(0, W, 64):
        d.rectangle([s(x), 0, s(x + 30), s(H)], fill=(252, 241, 216, 255))

    # Window with sky, clouds and curtains
    d.rounded_rectangle([s(80), s(60), s(340), s(330)], radius=s(10),
                        fill=(250, 250, 250, 255))
    for y in range(s(74), s(316)):
        k = (y - s(74)) / (s(316) - s(74))
        d.line([(s(94), y), (s(326), y)],
               fill=(int(140 + 80 * k), int(200 + 40 * k), 255, 255))
    for cx, cy in [(150, 130), (180, 122), (205, 134), (260, 220), (285, 212)]:
        ell(d, cx, cy, 26, 16, (255, 255, 255, 235))
    d.rectangle([s(205), s(74), s(215), s(316)], fill=(250, 250, 250, 255))
    d.rectangle([s(94), s(190), s(326), s(200)], fill=(250, 250, 250, 255))
    for side in (0, 1):
        x0 = 60 if side == 0 else 300
        poly(d, [(x0, 50), (x0 + 60, 50), (x0 + 40 - 10 * side, 340),
                 (x0 + 4, 345)], (232, 120, 104, 255))
        for i in range(3):
            xx = x0 + 14 + i * 14
            d.line([(s(xx), s(52)), (s(xx - 4 + 6 * side), s(340))],
                   fill=(206, 96, 84, 255), width=s(2))
    d.rectangle([s(50), s(40), s(370), s(52)], fill=(150, 98, 64, 255))
    # windowsill plant
    d.rectangle([s(70), s(330), s(350), s(342)], fill=(236, 226, 206, 255))
    poly(d, [(240, 330), (290, 330), (282, 296), (248, 296)],
         (196, 112, 76, 255))
    for a in range(-60, 61, 30):
        r = math.radians(a - 90)
        ell(d, 265 + 30 * math.cos(r), 280 + 26 * math.sin(r), 14, 9,
            (92, 160, 88, 255))

    # Picture frame on the right wall
    d.rounded_rectangle([s(1010), s(90), s(1190), s(230)], radius=s(6),
                        fill=(160, 112, 70, 255))
    d.rectangle([s(1022), s(102), s(1178), s(218)], fill=(255, 248, 232, 255))
    ell(d, 1100, 160, 34, 34, (255, 196, 86, 255))
    poly(d, [(1022, 218), (1070, 170), (1110, 218)], (126, 178, 120, 255))
    poly(d, [(1080, 218), (1130, 160), (1178, 218)], (96, 150, 104, 255))

    # Chair back behind the dog
    d.rounded_rectangle([s(470), s(220), s(810), s(500)], radius=s(40),
                        fill=(138, 86, 52, 255))
    d.rounded_rectangle([s(492), s(242), s(788), s(500)], radius=s(30),
                        fill=(160, 104, 66, 255))
    for x in (560, 640, 720):
        d.rounded_rectangle([s(x - 12), s(250), s(x + 12), s(500)],
                            radius=s(8), fill=(138, 86, 52, 255))

    # Pendant lamp with warm glow
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    ell(gd, 900, 150, 210, 170, (255, 214, 140, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(s(60)))
    img.alpha_composite(glow)
    d = ImageDraw.Draw(img)
    d.line([(s(900), 0), (s(900), s(110))], fill=(60, 50, 44, 255), width=s(3))
    poly(d, [(860, 110), (940, 110), (980, 160), (820, 160)],
         (232, 176, 80, 255))
    ell(d, 900, 160, 26, 10, (255, 244, 200, 255))
    return img


def build_table():
    img = Image.new("RGBA", (s(W), s(H)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    top = 470
    d.rectangle([0, s(top), s(W), s(H)], fill=(196, 138, 90, 255))
    for i, y in enumerate(range(top + 18, H, 26)):
        d.arc([s(-200 + 40 * (i % 3)), s(y - 8), s(W + 200), s(y + 30)],
              200, 340, fill=(176, 120, 76, 255), width=s(2))
    d.rectangle([0, s(top), s(W), s(top + 10)], fill=(220, 166, 116, 255))
    # gingham placemat
    mat = Image.new("RGBA", img.size, (0, 0, 0, 0))
    md = ImageDraw.Draw(mat)
    md.rounded_rectangle([s(380), s(488), s(930), s(690)], radius=s(18),
                         fill=(255, 255, 255, 255))
    for x in range(380, 930, 30):
        md.rectangle([s(x), s(488), s(x + 15), s(690)],
                     fill=(206, 226, 246, 255))
    for y in range(488, 690, 30):
        md.rectangle([s(380), s(y), s(930), s(y + 15)],
                     fill=(206, 226, 246, 255))
        for x in range(380, 930, 30):
            md.rectangle([s(x), s(y), s(x + 15), s(y + 15)],
                         fill=(160, 196, 232, 255))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [s(380), s(488), s(930), s(690)], radius=s(18), fill=255)
    clipped = Image.new("RGBA", img.size, (0, 0, 0, 0))
    clipped.paste(mat, (0, 0), mask)
    img.alpha_composite(clipped)
    d = ImageDraw.Draw(img)

    # glass of orange juice and a fork
    ell(d, 1040, 600, 46, 10, (120, 80, 50, 80))
    d.rounded_rectangle([s(1004), s(470), s(1076), s(600)], radius=s(10),
                        fill=(230, 240, 250, 150))
    d.rounded_rectangle([s(1010), s(508), s(1070), s(594)], radius=s(8),
                        fill=(255, 168, 48, 230))
    ell(d, 1040, 508, 30, 6, (255, 196, 96, 255))
    d.line([(s(1060), s(476)), (s(1060), s(590))],
           fill=(255, 255, 255, 160), width=s(4))
    d.rounded_rectangle([s(946), s(560), s(956), s(670)], radius=s(4),
                        fill=(200, 204, 210, 255))
    for k in range(4):
        d.rectangle([s(942 + k * 6), s(530), s(945 + k * 6), s(565)],
                    fill=(200, 204, 210, 255))
    return img


# ---------------------------------------------------------------- food
YOGURT_C = (520, 560)
SALAD_C = (780, 570)
BERRIES = [(-30, -6), (-6, -14), (22, -4), (8, 6), (-22, 8), (36, 8)]
SALAD_BITS = [
    ("leaf", -48, -10, 34), ("leaf", 0, -22, 36), ("leaf", 42, -8, 32),
    ("leaf", -20, 10, 30), ("leaf", 26, 14, 30),
    ("tomato", -30, -4, 12), ("tomato", 30, -14, 12), ("tomato", 6, 12, 12),
    ("cuke", -8, -6, 13), ("cuke", 50, 10, 12), ("cuke", -52, 12, 12),
    ("feta", 14, -4, 8), ("feta", -38, -14, 8), ("feta", 40, 2, 7),
]


def draw_yogurt(d, level, eaten_berries):
    cx, cy = YOGURT_C
    ell(d, cx, cy + 46, 92, 14, (110, 70, 40, 70))
    # bowl body
    d.chord([s(cx - 88), s(cy - 40), s(cx + 88), s(cy + 80)], 0, 180,
            fill=(118, 170, 214, 255))
    ell(d, cx, cy - 4, 88, 26, (96, 146, 196, 255))
    # yogurt surface (shrinks as it is eaten)
    ry = 20 * (0.6 + 0.4 * level)
    rx = 78 * (0.75 + 0.25 * level)
    ell(d, cx, cy - 2 + (1 - level) * 8, rx, ry, (252, 251, 246, 255))
    ell(d, cx - 18, cy - 8 + (1 - level) * 8, rx * 0.45, ry * 0.4,
        (255, 255, 255, 255))
    # honey drizzle
    if level > 0.5:
        d.arc([s(cx - 44), s(cy - 16), s(cx + 30), s(cy + 8)], 190, 350,
              fill=(232, 168, 40, 255), width=s(4))
    else:
        d.arc([s(cx - 20), s(cy - 6), s(cx + 26), s(cy + 10)], 200, 330,
              fill=(232, 168, 40, 255), width=s(3))
    for i, (bx, by) in enumerate(BERRIES):
        if i in eaten_berries:
            continue
        ell(d, cx + bx * (0.7 + 0.3 * level), cy + by * 0.9 + (1 - level) * 8,
            7, 7, (56, 70, 140, 255))
        ell(d, cx + bx * (0.7 + 0.3 * level) - 2,
            cy + by * 0.9 + (1 - level) * 8 - 2, 2, 2, (150, 160, 220, 255))
    # granola sprinkle
    for gx, gy in [(30, -12), (-40, 0), (44, -2), (-10, 8)]:
        if level > 0.5:
            ell(d, cx + gx, cy + gy, 5, 4, (210, 150, 80, 255))


def draw_yogurt_front(d):
    cx, cy = YOGURT_C
    d.chord([s(cx - 88), s(cy - 40), s(cx + 88), s(cy + 80)], 10, 170,
            fill=(118, 170, 214, 255))
    d.arc([s(cx - 88), s(cy - 30), s(cx + 88), s(cy + 22)], 0, 180,
          fill=(150, 196, 232, 255), width=s(4))
    d.arc([s(cx - 70), s(cy + 10), s(cx + 70), s(cy + 66)], 30, 70,
          fill=(200, 226, 246, 255), width=s(4))


def draw_salad(d, eaten):
    cx, cy = SALAD_C
    ell(d, cx, cy + 34, 112, 18, (110, 70, 40, 70))
    ell(d, cx, cy + 10, 110, 36, (236, 236, 236, 255))
    ell(d, cx, cy + 6, 108, 34, (255, 255, 255, 255))
    ell(d, cx, cy + 8, 78, 22, (244, 244, 244, 255))
    for i, (kind, bx, by, r) in enumerate(SALAD_BITS):
        if i in eaten:
            continue
        x, y = cx + bx, cy + by - 4
        if kind == "leaf":
            ell(d, x, y, r, r * 0.55, (110, 186, 84, 255))
            ell(d, x - 4, y - 3, r * 0.7, r * 0.35, (150, 212, 108, 255))
            d.line([(s(x - r * 0.7), s(y)), (s(x + r * 0.7), s(y - 2))],
                   fill=(208, 240, 170, 255), width=s(2))
        elif kind == "tomato":
            ell(d, x, y, r, r, (226, 58, 48, 255))
            ell(d, x - 4, y - 4, 3, 3, (255, 160, 150, 255))
        elif kind == "cuke":
            ell(d, x, y, r, r * 0.8, (96, 150, 70, 255))
            ell(d, x, y, r - 3, r * 0.8 - 3, (214, 240, 170, 255))
        else:
            d.rectangle([s(x - r), s(y - r * 0.8), s(x + r), s(y + r * 0.8)],
                        fill=(255, 255, 250, 255), outline=(220, 220, 210, 255))


def draw_salad_front(d):
    cx, cy = SALAD_C
    d.chord([s(cx - 110), s(cy - 26), s(cx + 110), s(cy + 46)], 15, 165,
            fill=(255, 255, 255, 255))
    d.arc([s(cx - 110), s(cy - 26), s(cx + 110), s(cy + 46)], 15, 165,
          fill=(226, 226, 226, 255), width=s(3))


# ---------------------------------------------------------------- the dog
HEAD_CANVAS = 460
HC = HEAD_CANVAS / 2


def head_layer(state):
    img = Image.new("RGBA", (s(HEAD_CANVAS), s(HEAD_CANVAS)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = HC
    twitch = state["ear_twitch"]
    # ears (behind the fluff)
    for side in (-1, 1):
        base_x = c + side * 58
        tip = (c + side * (74 + twitch * 6 * side), c - 138 + abs(twitch) * 6)
        outer = [(base_x - 30, c - 60), tip, (base_x + 30, c - 70)]
        poly(d, outer, FUR_SHADE)
        inner = [(base_x - 22 + 4, c - 66), (tip[0], tip[1] + 14),
                 (base_x + 22 - 4, c - 72)]
        poly(d, [(x, y) for x, y in outer], FUR)
        poly(d, inner, (248, 196, 196, 255))
    # head fluff: core plus ring of tufts and cheek puffs
    circles = [(c, c, 92)]
    for k in range(18):
        a = math.radians(k * 20 + 5)
        rr = 86 + (6 if k % 2 else 0)
        circles.append((c + rr * math.cos(a), c + rr * 0.92 * math.sin(a),
                        26 if k % 2 else 22))
    circles += [(c - 70, c + 50, 40), (c + 70, c + 50, 40), (c, c + 78, 44)]
    fluffy(d, circles)
    # little forehead tufts
    for dx, dy, r in [(-26, -84, 18), (0, -92, 20), (26, -84, 18)]:
        ell(d, c + dx, c + dy, r, r, FUR)
    # muzzle
    ell(d, c, c + 46, 56, 40, FUR_MID)
    ell(d, c, c + 42, 52, 36, FUR)
    # eyes
    for side in (-1, 1):
        ex, ey = c + side * 44, c - 4
        ell(d, ex, ey - 22, 22, 9, FUR_MID)  # fluffy brow
        if state["blink"]:
            d.arc([s(ex - 14), s(ey - 8), s(ex + 14), s(ey + 10)], 20, 160,
                  fill=BLACK, width=s(4))
        elif state["happy_eyes"]:
            d.arc([s(ex - 14), s(ey - 4), s(ex + 14), s(ey + 18)], 200, 340,
                  fill=BLACK, width=s(5))
        else:
            ell(d, ex, ey, 14, 15, BLACK)
            ell(d, ex - 4, ey - 6, 5, 5, (255, 255, 255, 255))
            ell(d, ex + 5, ey + 4, 2, 2, (255, 255, 255, 200))
    # blush
    for side in (-1, 1):
        ell(d, c + side * 70, c + 30, 16, 9, (255, 170, 180, 110))
    # mouth
    mx, my = c, c + 58
    open_amt = state["mouth_open"]
    if open_amt > 0.05:
        h = 6 + 22 * open_amt
        ell(d, mx, my + h * 0.5, 22, h, (110, 36, 48, 255))
        ell(d, mx, my + h * 0.9, 15, h * 0.5, PINK)
    else:
        d.arc([s(mx - 24), s(my - 14), s(mx + 2), s(my + 10)], 10, 170,
              fill=(90, 70, 70, 255), width=s(3))
        d.arc([s(mx - 2), s(my - 14), s(mx + 24), s(my + 10)], 10, 170,
              fill=(90, 70, 70, 255), width=s(3))
    if state["lick"] > 0:
        lk = state["lick"]
        tx = mx + 16 * math.sin(lk * math.pi * 2)
        ell(d, tx, my + 2 - 12 * math.sin(lk * math.pi), 12, 16, PINK)
        d.line([(s(tx), s(my - 4)), (s(tx), s(my + 10))], fill=DARK_PINK,
               width=s(2))
    if state["lettuce"]:
        sway = state["lettuce_sway"]
        leaf = [(mx + 14, my + 6), (mx + 46, my + 2 + sway),
                (mx + 72, my + 22 + sway), (mx + 56, my + 40 + sway),
                (mx + 26, my + 26)]
        poly(d, leaf, (118, 190, 88, 255))
        d.line([(s(mx + 16), s(my + 10)), (s(mx + 64), s(my + 26 + sway))],
               fill=(196, 234, 160, 255), width=s(3))
    # nose (drawn last so it sits on top)
    ell(d, c, c + 32, 19, 14, BLACK)
    ell(d, c - 6, c + 27, 6, 4, (110, 110, 120, 255))
    if state["yogurt_nose"]:
        ell(d, c + 10, c + 22, 13, 8, (255, 255, 252, 255),
            outline=(220, 220, 214, 255), width=1.5)
        ell(d, c - 22, c + 46, 7, 5, (255, 255, 252, 255),
            outline=(220, 220, 214, 255), width=1.5)
    # bib collar
    return img


def draw_body(d, lean, dy, t):
    bx = 640 + lean
    # tail (wagging, behind body)
    wag = math.radians(28 * math.sin(2 * math.pi * 3.2 * t))
    base = (bx + 92, 420)
    for k in range(5):
        a = math.radians(-60) + wag
        dist = 20 + k * 14
        ell(d, base[0] + dist * math.cos(a), base[1] + dist * math.sin(a),
            19 - k * 2 + 3.5, 19 - k * 2 + 3.5, FUR_SHADE)
    for k in range(5):
        a = math.radians(-60) + wag
        dist = 20 + k * 14
        ell(d, base[0] + dist * math.cos(a), base[1] + dist * math.sin(a),
            19 - k * 2, 19 - k * 2, FUR)
    by = dy  # vertical shift of the upper body while leaning into a dish
    circles = [(bx, 440 + by * 0.4, 112)]
    for k in range(14):
        a = math.radians(180 + k * (180 / 13))
        circles.append((bx + 108 * math.cos(a),
                        440 + by * 0.4 + 100 * math.sin(a), 26))
    circles += [(bx - 40, 360 + by, 50), (bx + 40, 360 + by, 50)]
    fluffy(d, circles)
    # chest fluff
    for fx, fy in [(-30, 380), (0, 395), (30, 380), (-12, 420), (14, 422)]:
        ell(d, bx + fx, fy + by, 22, 22, FUR_MID)
        ell(d, bx + fx, fy + by - 2, 20, 20, FUR)
    # red napkin bib with white polka dots
    poly(d, [(bx - 70, 352 + by), (bx + 70, 352 + by), (bx, 448 + by)],
         (214, 60, 60, 255))
    for px, py in [(-40, 362), (0, 368), (40, 362), (-18, 392), (20, 392),
                   (0, 420)]:
        ell(d, bx + px, py + by, 5, 5, (255, 236, 236, 255))
    d.rounded_rectangle([s(bx - 76), s(344 + by), s(bx + 76), s(360 + by)],
                        radius=s(8), fill=(190, 44, 48, 255))


def draw_paws(d, lean, t, reach):
    for side, x0 in ((-1, 586), (1, 694)):
        x = x0 + lean * 0.6 + (reach * 10 * side if reach else 0)
        y = 486 + (2 * math.sin(2 * math.pi * 2 * t + side) if side else 0)
        ell(d, x, y, 34, 22, FUR_SHADE)
        ell(d, x, y - 2, 31, 19, FUR)
        for k in (-1, 0, 1):
            d.line([(s(x + k * 10), s(y + 4)), (s(x + k * 10), s(y + 16))],
                   fill=FUR_SHADE, width=s(2))


def heart(d, cx, cy, size, alpha):
    col = (240, 80, 110, int(255 * alpha))
    r = size * 0.32
    ell(d, cx - r, cy - r * 0.4, r, r, col)
    ell(d, cx + r, cy - r * 0.4, r, r, col)
    poly(d, [(cx - 2 * r, cy - r * 0.1), (cx + 2 * r, cy - r * 0.1),
             (cx, cy + size * 0.7)], col)


def sparkle(d, cx, cy, size, alpha):
    col = (255, 214, 90, int(255 * alpha))
    poly(d, [(cx, cy - size), (cx + size * 0.25, cy), (cx, cy + size),
             (cx - size * 0.25, cy)], col)
    poly(d, [(cx - size, cy), (cx, cy + size * 0.25), (cx + size, cy),
             (cx, cy - size * 0.25)], col)


# ---------------------------------------------------------------- timeline
HEAD_KEYS = [  # t, x, y, angle(deg, ccw+)
    (0.00, 640, 262, 0),
    (0.45, 646, 258, -6),
    (0.85, 636, 262, 5),
    (1.30, 548, 452, 16),
    (1.70, 548, 458, 16),
    (2.05, 632, 268, 4),
    (2.55, 640, 262, -3),
    (2.95, 768, 462, -16),
    (3.35, 768, 466, -16),
    (3.70, 650, 268, -4),
    (4.40, 636, 260, 6),
    (5.00, 640, 262, 0),
]


def state_at(t):
    x, y, ang = interp_keys(HEAD_KEYS, t)
    y += 3 * math.sin(2 * math.pi * 1.1 * t)
    st = {
        "blink": any(window(t, a, a + 0.12) for a in (0.62, 2.62, 4.75)),
        "happy_eyes": window(t, 1.75, 2.35) or window(t, 3.75, 4.6),
        "ear_twitch": math.sin(2 * math.pi * 1.6 * t) * (
            1.0 if window(t, 0, 1.2) or window(t, 3.7, 5) else 0.3),
        "mouth_open": 0.0,
        "lick": 0.0,
        "lettuce": window(t, 3.3, 4.1),
        "lettuce_sway": 6 * math.sin(2 * math.pi * 5 * t),
        "yogurt_nose": window(t, 1.55, 2.45),
    }
    # mouth: open while dipping, chewing afterwards
    if window(t, 1.1, 1.75) or window(t, 2.75, 3.4):
        st["mouth_open"] = 0.55 + 0.35 * math.sin(2 * math.pi * 6 * t)
    elif window(t, 1.75, 2.25) or window(t, 3.4, 4.1):
        st["mouth_open"] = max(0.0, math.sin(2 * math.pi * 4.5 * t)) * 0.6
    elif window(t, 0.2, 0.55):
        st["mouth_open"] = 0.35  # excited little pant
    if window(t, 2.25, 2.6):
        st["lick"] = (t - 2.25) / 0.35
    elif window(t, 4.2, 4.6):
        st["lick"] = (t - 4.2) / 0.4
    yogurt_level = 1.0 - 0.45 * smooth((t - 1.3) / 0.45)
    eaten_berries = {1, 4} if t > 1.5 else set()
    eaten_salad = {1, 6, 8} if t > 3.15 else set()
    return (x, y, ang), st, yogurt_level, eaten_berries, eaten_salad


def render_frame(t, bg, table):
    (hx, hy, ang), st, ylevel, eberries, esalad = state_at(t)
    img = bg.copy()
    d = ImageDraw.Draw(img)
    lean = (hx - 640) * 0.28
    draw_body(d, lean, (hy - 262) * 0.45, t)
    img.alpha_composite(table)
    d = ImageDraw.Draw(img)
    draw_paws(d, lean, t, 0)
    draw_yogurt(d, ylevel, eberries)
    draw_salad(d, esalad)

    head = head_layer(st).rotate(ang, resample=Image.BICUBIC)
    img.alpha_composite(head, (s(hx - HC), s(hy - HC)))
    d = ImageDraw.Draw(img)
    if hy > 380:  # head is down in a dish: redraw its front rim over the snout
        if hx < 640:
            draw_yogurt_front(d)
        else:
            draw_salad_front(d)

    fx = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(fx)
    for i, start in enumerate((3.9, 4.15, 4.4)):
        if t > start:
            u = (t - start) / 1.1
            if u < 1:
                hx2 = 640 + (-110, 120, -40)[i] + 14 * math.sin(u * 7 + i)
                heart(fd, hx2, 170 - 120 * u, 34 + 8 * i, 1 - u * u)
    for i, start in enumerate((1.8, 2.0, 3.45, 3.6)):
        if start < t < start + 0.6:
            u = (t - start) / 0.6
            sx = (560, 720, 590, 740)[i]
            sparkle(fd, sx + 20 * u * (1 if i % 2 else -1), 150 - 30 * u,
                    16 * math.sin(u * math.pi), 1.0)
    img.alpha_composite(fx)
    return img.convert("RGB").resize((W, H), Image.LANCZOS)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "white_terrier_eating.mp4"
    bg = build_background()
    table = build_table()
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo",
         "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
         "-preset", "slow", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)
    for i in range(FRAMES):
        frame = render_frame(i / FPS, bg, table)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()
    if proc.returncode:
        sys.exit(proc.returncode)
    print(f"wrote {out} ({FRAMES} frames, {DURATION}s @ {FPS}fps)")


if __name__ == "__main__":
    main()
