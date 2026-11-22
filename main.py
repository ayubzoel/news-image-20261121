#!/usr/bin/env python3
"""The World in One Day — Saturday, 21 November 2026.

Draws a single 1024x1024 newspaper-style poster summing up the world news
of Saturday 21 November 2026, using only the Python standard library and
Pillow. No network access, no timestamps, no randomness: running it twice
produces byte-identical output.

Layout (1024 x 1024):
  masthead 0-118   title + date
  hero 118-268     lead story: APEC Shenzhen (Trump, Xi, Putin)
  map 268-548      world map, every story pinned and numbered
  top stories 548-884   15 main stories in two columns
  also today 884-1006   20 more stories in three columns
  footer 1006-1024      dateline strip

Output: $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).
"""

import hashlib
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
CREAM = (246, 241, 231)
INK = (22, 19, 14)
RED = (179, 38, 30)
RED_DARK = (140, 28, 22)
NAVY = (21, 38, 71)
NAVY_DARK = (13, 24, 48)
NAVY_PIN = (31, 58, 102)
GOLD = (232, 163, 23)
GOLD_SOFT = (240, 200, 110)
OCEAN = (199, 216, 230)
LAND = (233, 217, 174)
LAND_EDGE = (138, 122, 82)
GRID = (172, 196, 213)
GRAY = (92, 88, 79)
BAND = (227, 233, 238)
WHITE = (255, 255, 255)
SKYLINE = (9, 18, 36)

# ---------------------------------------------------------------- fonts
_FONT_DIR = "/usr/share/fonts/truetype/dejavu/"
_FONT_PATHS = {
    "serif_b": _FONT_DIR + "DejaVuSerif-Bold.ttf",
    "sans_b": _FONT_DIR + "DejaVuSans-Bold.ttf",
    "sans": _FONT_DIR + "DejaVuSans.ttf",
}
_FONT_CACHE = {}


def font(kind, size):
    key = (kind, size)
    if key not in _FONT_CACHE:
        path = _FONT_PATHS[kind]
        if os.path.exists(path):
            _FONT_CACHE[key] = ImageFont.truetype(path, size)
        else:  # pragma: no cover - environment fallback
            _FONT_CACHE[key] = ImageFont.load_default()
    return _FONT_CACHE[key]


# ---------------------------------------------------------------- text helpers
def text_w(draw, text, fnt):
    return draw.textlength(text, font=fnt)


def draw_centered(draw, cx, y, text, fnt, fill):
    draw.text((cx - text_w(draw, text, fnt) / 2, y), text, font=fnt, fill=fill)


def draw_spaced_centered(draw, cx, y, text, fnt, fill, spacing):
    """Draw text with extra tracking, centred on cx."""
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += w + spacing


def wrap(text, fnt, max_w, draw):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- map data
# Simplified continent outlines (lon, lat). Deliberately coarse: the map is
# a locator graphic, pins carry the meaning. The Americas are one ring:
# Pacific coast south to Panama, Caribbean coast back west to Yucatan,
# Gulf, Florida, Atlantic coast north, Arctic, Alaska.
AMERICAS = [
    (-168, 66), (-158, 58), (-145, 60), (-135, 58), (-130, 54), (-125, 48),
    (-124, 40), (-120, 34), (-114, 29), (-110, 23), (-105, 20), (-97, 16),
    (-94, 17), (-90, 14), (-87, 13), (-83, 10), (-80, 8), (-79, 9),
    (-77, 5), (-80, 0), (-81, -4), (-80, -8), (-77, -12), (-75, -15),
    (-72, -18), (-70, -22), (-70, -28), (-72, -33), (-73, -38), (-73, -44),
    (-73, -50), (-71, -54), (-68, -55), (-65, -52), (-63, -47), (-62, -42),
    (-58, -38), (-55, -34), (-52, -32), (-48, -28), (-44, -24), (-40, -21),
    (-38, -15), (-35, -8), (-38, -5), (-44, -3), (-48, -1), (-50, 0),
    (-52, 4), (-55, 6), (-58, 8), (-61, 10), (-64, 11), (-68, 12),
    (-72, 13), (-76, 15), (-80, 16), (-84, 16), (-87, 16), (-88, 18),
    (-87, 21), (-90, 21), (-94, 19), (-97, 22), (-97, 26), (-94, 29),
    (-90, 30), (-86, 30), (-82, 31), (-80, 32), (-77, 35), (-75, 38),
    (-74, 40), (-70, 42), (-68, 44), (-65, 44), (-61, 46), (-58, 49),
    (-55, 52), (-53, 55), (-55, 58), (-58, 61), (-62, 63), (-66, 65),
    (-70, 68), (-76, 71), (-82, 73), (-88, 74), (-95, 73), (-102, 72),
    (-110, 70), (-118, 70), (-126, 71), (-134, 70), (-142, 70), (-150, 70),
    (-158, 68), (-164, 66),
]
GREENLAND = [
    (-58, 64), (-52, 60), (-45, 60), (-40, 64), (-32, 68), (-25, 70),
    (-30, 74), (-38, 76), (-50, 76), (-58, 74), (-60, 70), (-58, 64),
]
AFRICA = [
    (-17, 15), (-16, 20), (-13, 27), (-9, 31), (-6, 34), (-2, 35),
    (2, 36), (6, 37), (10, 37), (15, 34), (19, 32), (23, 33), (27, 32),
    (30, 31), (32, 31), (34, 28), (35, 25), (37, 20), (39, 16), (41, 12),
    (44, 11), (48, 11), (51, 12), (48, 8), (45, 4), (42, 0), (40, -3),
    (39, -8), (37, -12), (36, -18), (34, -22), (32, -26), (29, -30),
    (27, -33), (24, -34), (20, -35), (18, -32), (16, -28), (14, -22),
    (13, -17), (12, -12), (11, -7), (9, -3), (9, 2), (8, 4), (4, 6),
    (0, 6), (-5, 5), (-8, 4), (-12, 7), (-15, 11), (-17, 15),
]
EURASIA = [
    (-10, 36), (-9, 39), (-9, 43), (-4, 48), (-1, 49), (2, 51), (4, 53),
    (7, 55), (8, 57), (10, 59), (12, 57), (16, 56), (18, 56), (21, 55),
    (24, 58), (27, 59), (29, 60), (30, 62), (32, 64), (34, 66), (38, 68),
    (44, 68), (50, 69), (56, 69), (62, 70), (68, 72), (74, 73), (80, 73),
    (86, 74), (95, 76), (104, 77), (112, 75), (120, 73), (128, 72),
    (136, 72), (144, 71), (152, 70), (160, 69), (168, 67), (173, 66),
    (178, 65), (173, 63), (169, 60), (163, 60), (160, 55), (157, 52),
    (153, 49), (148, 46), (144, 43), (141, 40), (140, 36), (137, 35),
    (134, 34), (131, 33), (129, 32), (127, 35), (126, 38), (123, 39),
    (121, 37), (120, 32), (118, 28), (115, 24), (110, 20), (108, 16),
    (106, 10), (104, 8), (101, 7), (99, 10), (98, 14), (96, 16),
    (94, 18), (92, 21), (90, 22), (88, 22), (86, 20), (83, 18),
    (80, 15), (78, 9), (77, 8), (75, 10), (73, 16), (72, 20),
    (70, 22), (68, 23), (66, 25), (63, 25), (60, 25), (57, 26),
    (55, 27), (52, 26), (50, 29), (48, 30), (46, 30), (44, 29),
    (42, 30), (39, 30), (36, 31), (35, 33), (34, 36), (32, 36),
    (30, 36), (27, 37), (26, 38), (23, 36), (21, 37), (19, 40),
    (17, 40), (15, 44), (13, 44), (11, 44), (8, 44), (6, 43),
    (3, 43), (0, 40), (-2, 37), (-6, 36), (-9, 37), (-10, 36),
]
UNITED_KINGDOM = [
    (-5, 50), (-3, 53), (-5, 56), (-4, 58), (-2, 58), (0, 57), (0, 53),
    (1, 51), (-2, 51), (-4, 50), (-5, 50),
]
JAPAN = [
    (130, 31), (132, 33), (134, 34), (136, 34), (138, 35), (139, 36),
    (140, 38), (141, 40), (141, 42), (142, 44), (144, 44), (143, 41),
    (141, 39), (140, 36), (138, 35), (136, 33), (134, 33), (132, 32),
    (130, 31),
]
AUSTRALIA = [
    (113, -22), (114, -27), (115, -32), (116, -35), (119, -34), (122, -33),
    (126, -32), (129, -32), (132, -33), (133, -35), (136, -35), (138, -37),
    (140, -38), (143, -39), (146, -39), (149, -37), (151, -35), (153, -32),
    (153, -28), (151, -24), (149, -20), (147, -19), (145, -17), (143, -14),
    (142, -11), (140, -14), (138, -15), (136, -14), (135, -13), (133, -12),
    (131, -12), (129, -14), (127, -14), (124, -16), (122, -17), (119, -19),
    (116, -20), (113, -22),
]
NEW_ZEALAND = [
    (167, -45), (169, -43), (171, -41), (173, -40), (175, -38), (177, -38),
    (176, -40), (174, -41), (172, -43), (170, -45), (167, -45),
]
MADAGASCAR = [
    (44, -16), (47, -15), (50, -16), (50, -20), (48, -24), (45, -25),
    (44, -22), (43, -18), (44, -16),
]
BORNEO = [
    (109, 1), (111, 3), (113, 4), (116, 6), (118, 4), (119, 1),
    (117, -3), (114, -4), (111, -3), (109, 0), (109, 1),
]
SUMATRA = [
    (95, 5), (98, 4), (101, 1), (103, -2), (105, -4), (106, -6),
    (104, -5), (102, -2), (99, 1), (97, 4), (95, 5),
]
JAVA = [
    (105, -6), (108, -7), (111, -7), (114, -7), (113, -8), (110, -8),
    (107, -8), (105, -7), (105, -6),
]
NEW_GUINEA = [
    (131, -1), (134, -2), (137, -3), (140, -4), (141, -6), (139, -8),
    (136, -8), (133, -6), (131, -3), (131, -1),
]
ICELAND = [
    (-22, 64), (-18, 63), (-14, 64), (-15, 66), (-19, 66), (-22, 65),
    (-22, 64),
]
SRI_LANKA = [
    (80, 9), (81, 8), (81, 6), (80, 6), (79, 8), (80, 9),
]
TAIWAN = [
    (120, 22), (121, 23), (121, 25), (120, 25), (120, 23), (120, 22),
]
CUBA = [
    (-85, 22), (-80, 23), (-75, 21), (-74, 20), (-77, 21), (-82, 22),
    (-85, 22),
]

LAND_POLYS = [
    AMERICAS, GREENLAND, AFRICA, EURASIA,
    UNITED_KINGDOM, JAPAN, AUSTRALIA, NEW_ZEALAND, MADAGASCAR,
    BORNEO, SUMATRA, JAVA, NEW_GUINEA, ICELAND, SRI_LANKA, TAIWAN, CUBA,
]

# ---------------------------------------------------------------- story data
# Main stories: n, headline, one-line summary, pin lon/lat.
# draw=(lon, lat) overrides the drawn pin position when the true spot is
# crowded; a thin leader line then points back to the true spot.
MAIN = [
    (1, "Trump, Xi and Putin meet in Shenzhen",
     "First three-way meeting; nuclear-risk talks to begin.", 114.06, 22.55, None),
    (2, "Iran strikes Bahrain site",
     "Fire at an industrial site; no casualties; Bahrain seeks redress.", 50.56, 26.23, (47.0, 28.5)),
    (3, "Hormuz tanker attacks hit wartime high",
     "Two more tankers hit; oil flow through the strait down 15%.", 56.5, 26.6, None),
    (4, "Trump warns Iran over chemical weapons",
     "Vows military action if Iran targets Washington; Iran denies it.", -77.04, 38.9, (-82.0, 36.0)),
    (5, "COP31 deadlocked in overtime",
     "Talks run a second day over as fossil wording is cut from draft.", 30.71, 36.88, None),
    (6, "US stocks slide into correction",
     "AI sell-off pushes the S&P 500 down 3.7%; the Dow follows suit.", -74.0, 40.71, None),
    (7, "Nvidia halts H200 chips to China",
     "Exports stopped amid the US debate over advanced AI chip sales.", -121.95, 37.35, (-114.0, 33.5)),
    (8, "Mexico captures 'El Chapo Isidro'",
     "FBI most-wanted cartel boss held in Sinaloa; 11 killed.", -107.4, 24.8, None),
    (9, "Russia hits Kryvyi Rih; Kyiv hits ship",
     "Two killed, dozens hurt; a Russia-bound ship burns.", 33.39, 47.91, None),
    (10, "Magnitude 6.7 quake shakes Peru",
     "Strong quake hits the central Andes; no casualties reported.", -75.0, -10.0, None),
    (11, "ICJ: Myanmar guilty of genocide",
     "Court rules 9-6 on the Rohingya - a first for a state.", 96.15, 16.8, None),
    (12, "AI helps prove Riemann hypothesis",
     "An Anthropic researcher says AI helped crack maths' top puzzle.", -122.42, 37.77, None),
    (13, "Bolsonaro in intensive care",
     "Brazil's ex-president hospitalised with a bowel obstruction.", -47.93, -15.79, None),
    (14, "UK and EU seal post-Brexit reset",
     "Deals on food, carbon and youth mobility after years of talks.", -0.13, 51.51, None),
    (15, "Nepal's PM makes first India visit",
     "Balendra Shah heads to New Delhi to meet Modi on his first trip.", 77.21, 28.61, None),
]

# Also today: n, one-line text, pin lon/lat, optional drawn position.
ALSO = [
    (16, "EU, Indonesia sign trade deal after 10 years", 4.35, 50.85, (8.0, 60.0)),
    (17, "Prabowo meets Xi; $71.8bn of deals agreed", 116.41, 39.9, None),
    (18, "Jakarta stocks fall 3.71% in a week", 106.85, -6.21, None),
    (19, "Indonesia closes its COP31 pavilion", 106.85, -6.21, (118.0, -9.0)),
    (20, "Hong Kong Open: four Indonesians in semis", 114.17, 22.32, (121.5, 20.5)),
    (21, "Jensen Huang to testify before US Senate", -77.8, 38.7, (-89.0, 34.5)),
    (22, "Gen Z walkouts sweep 25 European states", 13.4, 52.52, (26.0, 56.0)),
    (23, "Denmark backs US-Greenland deal, 109-0", 12.57, 55.68, (20.0, 62.0)),
    (24, "France enters a sixth week of protests", 2.35, 48.86, (1.0, 39.5)),
    (25, "FBI probes hack of its criminal database", -76.2, 39.6, (-67.0, 45.0)),
    (26, "Mamdani vows to close New York's Rikers", -74.0, 40.71, (-58.0, 37.0)),
    (27, "Floods swamp 850 homes in France", 4.83, 45.76, (14.0, 40.0)),
    (28, "Snow strands 1,000+ in Fukushima", 140.47, 37.76, None),
    (29, "Tainted alcohol kills 11 in Manipur", 93.94, 24.82, (100.0, 30.0)),
    (30, "Pakistani man jailed 27 years over Trump plot", 73.07, 33.68, (68.0, 36.0)),
    (31, "Russia uses GTA VI in army recruitment ads", 37.62, 55.76, None),
    (32, "Harry Kane out for months with injury", 11.58, 48.14, (22.0, 47.0)),
    (33, "FFI 2026: 'Para Perasuk' wins Best Film", 106.85, -6.21, (98.0, -10.0)),
    (34, "Honor teases phone with 15,000 mAh battery", 116.41, 39.9, (126.0, 33.0)),
    (35, "Taylor Swift wins a major award in India", 72.88, 19.08, None),
]

MAP_X, MAP_Y, MAP_W, MAP_H = 20, 268, 984, 280
LAT_TOP, LAT_BOT = 78.0, -58.0


def project(lon, lat):
    x = MAP_X + (lon + 180.0) / 360.0 * MAP_W
    y = MAP_Y + (LAT_TOP - lat) / (LAT_TOP - LAT_BOT) * MAP_H
    return (x, y)


def draw_star(draw, cx, cy, r_out, r_in, fill, outline):
    pts = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        ang = math.pi / 2 + i * math.pi / 5
        pts.append((cx + r * math.cos(ang), cy - r * math.sin(ang)))
    draw.polygon(pts, fill=fill, outline=outline)


def draw_flag_us(draw, x, y, w, h):
    stripe = h / 13.0
    for i in range(13):
        draw.rectangle([x, y + i * stripe, x + w, y + (i + 1) * stripe],
                       fill=RED if i % 2 == 0 else WHITE)
    canton_w, canton_h = w * 0.42, stripe * 7
    draw.rectangle([x, y, x + canton_w, y + canton_h], fill=NAVY)
    for row in range(5):
        for col in range(6):
            px = x + 4 + col * (canton_w - 8) / 5
            py = y + 4 + row * (canton_h - 8) / 4
            draw.ellipse([px - 1.1, py - 1.1, px + 1.1, py + 1.1], fill=WHITE)


def draw_flag_cn(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(222, 41, 16))
    draw_star(draw, x + w * 0.22, y + h * 0.28, 9, 3.8, GOLD, GOLD)
    for sx, sy in [(0.48, 0.12), (0.58, 0.26), (0.56, 0.46), (0.42, 0.52)]:
        draw_star(draw, x + w * sx, y + h * sy, 3.4, 1.5, GOLD, GOLD)


def draw_flag_ru(draw, x, y, w, h):
    third = h / 3.0
    draw.rectangle([x, y, x + w, y + third], fill=WHITE)
    draw.rectangle([x, y + third, x + w, y + 2 * third], fill=(0, 57, 166))
    draw.rectangle([x, y + 2 * third, x + w, y + h], fill=(213, 0, 50))


# ---------------------------------------------------------------- build
def build():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)

    # ---- masthead ------------------------------------------------------
    draw_centered(d, W // 2, 14, "THE WORLD IN ONE DAY",
                  font("serif_b", 54), INK)
    d.rectangle([28, 78, W - 28, 81], fill=RED)
    draw_spaced_centered(d, W // 2, 88, "SATURDAY, 21 NOVEMBER 2026",
                         font("sans_b", 23), RED, 3)

    # ---- hero band -----------------------------------------------------
    d.rectangle([0, 118, W, 268], fill=NAVY_DARK)
    d.rectangle([0, 118, W, 121], fill=GOLD)
    d.text((28, 132), "LEAD STORY  ·  SHENZHEN, CHINA",
           font=font("sans_b", 13), fill=GOLD)
    d.text((28, 156), "THREE LEADERS, ONE TABLE",
           font=font("serif_b", 34), fill=WHITE)
    hero_lines = wrap(
        "Trump, Xi and Putin hold a three-way meeting at the APEC summit "
        "and agree to open talks on reducing nuclear risk.",
        font("sans", 15), 592, d)
    yy = 206
    for line in hero_lines:
        d.text((28, yy), line, font=font("sans", 15), fill=(216, 222, 233))
        yy += 19
    # three flags over a Shenzhen skyline
    base_y = 258
    for fx, painter in ((648, draw_flag_us), (782, draw_flag_cn), (916, draw_flag_ru)):
        d.line([fx + 45, 138, fx + 45, base_y], fill=GOLD_SOFT, width=2)
        d.ellipse([fx + 41, 134, fx + 49, 142], fill=GOLD)
        painter(d, fx, 142, 90, 56)
    # skyline silhouette with lit windows
    skyline = [(648, 236, 664, 258), (666, 222, 686, 258), (688, 242, 704, 258),
               (706, 214, 728, 258), (730, 238, 748, 258), (750, 226, 772, 258),
               (774, 244, 790, 258), (792, 218, 814, 258), (816, 240, 834, 258),
               (836, 228, 856, 258), (858, 244, 876, 258), (878, 220, 900, 258),
               (902, 238, 920, 258), (922, 230, 942, 258), (944, 242, 962, 258),
               (964, 232, 980, 258), (982, 244, 996, 258)]
    for x0, y0, x1, y1 in skyline:
        d.rectangle([x0, y0, x1, y1], fill=SKYLINE)
        for wy in range(y0 + 6, y1 - 4, 12):
            for wx in range(x0 + 4, x1 - 4, 10):
                if (wx * 7 + wy * 13) % 5 < 2:
                    d.rectangle([wx, wy, wx + 3, wy + 4], fill=GOLD_SOFT)

    # ---- world map -----------------------------------------------------
    # Ocean, graticule and land are rendered at 2x on a scratch layer and
    # downscaled, so coastlines get real anti-aliasing instead of the
    # jagged 1x polygon edges.
    ss = 2
    layer = Image.new("RGB", (MAP_W * ss, MAP_H * ss), OCEAN)
    ld = ImageDraw.Draw(layer)
    for lon in range(-180, 181, 30):
        x = (lon + 180) / 360.0 * MAP_W * ss
        ld.line([x, 0, x, MAP_H * ss], fill=GRID, width=ss)
    for lat in range(-60, 79, 20):
        y = (LAT_TOP - lat) / (LAT_TOP - LAT_BOT) * MAP_H * ss
        ld.line([0, y, MAP_W * ss, y], fill=GRID, width=ss)
    for poly in LAND_POLYS:
        pts = [((lon + 180.0) / 360.0 * MAP_W * ss,
                (LAT_TOP - lat) / (LAT_TOP - LAT_BOT) * MAP_H * ss)
               for lon, lat in poly]
        ld.polygon(pts, fill=LAND, outline=LAND_EDGE)
    img.paste(layer.resize((MAP_W, MAP_H), Image.LANCZOS), (MAP_X, MAP_Y))
    d.rectangle([MAP_X, MAP_Y, MAP_X + MAP_W, MAP_Y + MAP_H],
                outline=INK, width=2)
    # leaders first (under the pins)
    pins = []
    for n, _h, _s, lon, lat, draw_at in MAIN:
        pins.append((n, lon, lat, draw_at, True))
    for n, _t, lon, lat, draw_at in ALSO:
        pins.append((n, lon, lat, draw_at, False))
    for n, lon, lat, draw_at, is_main in pins:
        if draw_at is not None:
            tx, ty = project(lon, lat)
            dx, dy = project(*draw_at)
            d.line([dx, dy, tx, ty], fill=(90, 90, 90), width=1)
            d.ellipse([tx - 2, ty - 2, tx + 2, ty + 2], fill=INK)
    # pins
    for n, lon, lat, draw_at, is_main in pins:
        px, py = project(*(draw_at if draw_at is not None else (lon, lat)))
        if n == 1:
            draw_star(d, px, py, 14, 6, RED, RED_DARK)
            num = font("sans_b", 11)
            tw = d.textlength("1", font=num)
            d.text((px - tw / 2, py - 8), "1", font=num, fill=WHITE)
        else:
            r = 10 if is_main else 7.5
            fill = RED if is_main else NAVY_PIN
            d.ellipse([px - r, py - r, px + r, py + r], fill=fill,
                      outline=WHITE, width=1)
            num = font("sans_b", 11 if is_main else 9)
            label = str(n)
            tw = d.textlength(label, font=num)
            th = 11 if is_main else 9
            d.text((px - tw / 2, py - th / 2 - 1), label, font=num, fill=WHITE)
    d.text((30, 524), "THE WORLD  —  EVERY STORY PINNED",
           font=font("sans_b", 13), fill=NAVY)

    # ---- top stories ---------------------------------------------------
    d.text((28, 556), "TOP STORIES", font=font("sans_b", 18), fill=INK)
    d.rectangle([28, 578, 996, 581], fill=RED)
    col_x = [28, 524]
    col_n = [MAIN[0:8], MAIN[8:15]]
    y0 = 590
    pitch = 36
    for ci in range(2):
        for i, (n, headline, summary, _lon, _lat, _da) in enumerate(col_n[ci]):
            y = y0 + i * pitch
            d.rounded_rectangle([col_x[ci], y, col_x[ci] + 18, y + 18],
                                radius=3, fill=RED)
            num = font("sans_b", 11)
            tw = d.textlength(str(n), font=num)
            d.text((col_x[ci] + 9 - tw / 2, y + 3), str(n), font=num, fill=WHITE)
            d.text((col_x[ci] + 26, y), headline, font=font("sans_b", 14), fill=INK)
            d.text((col_x[ci] + 26, y + 18), summary, font=font("sans", 12),
                   fill=GRAY)
            if text_w(d, summary, font("sans", 12)) > 446:
                print("OVERFLOW summary %d: %s" % (n, summary))
            if text_w(d, headline, font("sans_b", 14)) > 446:
                print("OVERFLOW headline %d: %s" % (n, headline))
    # day in numbers (fills the right column's spare rows)
    bx, by = 524, 848
    d.rectangle([bx, by, 996, 880], outline=INK, width=1)
    d.rectangle([bx, by, 996, 880], fill=(238, 232, 214))
    d.text((bx + 10, by + 3), "THE DAY IN NUMBERS",
           font=font("sans_b", 11), fill=RED)
    d.text((bx + 10, by + 16), "S&P -3.7%  ·  $1.7T lost  ·  Oil -15%  ·  11 dead  ·  M6.7",
           font=font("sans_b", 12), fill=INK)

    # ---- also today ----------------------------------------------------
    d.rectangle([0, 884, W, 1006], fill=BAND)
    d.rectangle([0, 884, W, 886], fill=INK)
    d.text((28, 892), "ALSO TODAY", font=font("sans_b", 15), fill=INK)
    d.rectangle([28, 914, 996, 916], fill=RED)
    cols = [ALSO[0:7], ALSO[7:14], ALSO[14:20]]
    col_x = [28, 352, 676]
    for ci, items in enumerate(cols):
        for i, (n, text, _lon, _lat, _da) in enumerate(items):
            y = 920 + i * 12
            d.text((col_x[ci], y), "%d." % n, font=font("sans_b", 11), fill=RED)
            d.text((col_x[ci] + 24, y), text, font=font("sans", 11), fill=INK)
            if text_w(d, text, font("sans", 11)) > 286:
                print("OVERFLOW also %d: %s" % (n, text))

    # ---- footer --------------------------------------------------------
    d.rectangle([0, 1006, W, H], fill=INK)
    draw_centered(d, W // 2, 1010,
                  "Saturday, 21 November 2026  ·  One day, one page  ·  "
                  "All facts as reported on the day",
                  font("sans", 10), (220, 216, 208))
    return img


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    img = build()
    path = os.path.join(out_dir, "entry.png")
    img.save(path, format="PNG")
    data = open(path, "rb").read()
    print("wrote %s %d bytes sha256=%s" % (
        path, len(data), hashlib.sha256(data).hexdigest()))


if __name__ == "__main__":
    main()
