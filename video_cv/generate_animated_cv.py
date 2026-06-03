#!/usr/bin/env python3
"""Generate a 90-second animated video CV for Dominika Romanow.

The script renders all visuals procedurally with Pillow and encodes the final
MP4 with FFmpeg. It can also mux an external voiceover file into the video.
"""

from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1280
HEIGHT = 720
FPS = 30
DURATION = 90.0

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "output" / "dominika_romanow_video_cv.mp4"
DEFAULT_SRT = ROOT / "output" / "dominika_romanow_video_cv.srt"


@dataclass(frozen=True)
class Scene:
    start: float
    end: float
    title: str
    kicker: str
    caption: str
    bg_top: tuple[int, int, int]
    bg_bottom: tuple[int, int, int]
    icon: str


SCENES: list[Scene] = [
    Scene(
        0,
        10,
        "Dominika Romanow",
        "Olsztyn -> HR",
        "Cześć, jestem Dominika Romanow. Pochodzę z Olsztyna i szukam pierwszej pracy w HR.",
        (255, 246, 232),
        (232, 245, 255),
        "intro",
    ),
    Scene(
        10,
        19,
        "Współpraca od dziecka",
        "bliźniaczka, negocjacje, dzielenie się",
        "Dorastałam z siostrą bliźniaczką, więc od małego ćwiczyłam negocjacje, współpracę i dzielenie się wszystkim.",
        (248, 241, 255),
        (255, 240, 244),
        "twins",
    ),
    Scene(
        19,
        29,
        "Pierwsze doświadczenie",
        "restauracja w Olsztynie",
        "Pierwszą szkołą tempa była restauracja: kontakt z ludźmi, organizacja i spokojne reagowanie w ruchu.",
        (237, 250, 245),
        (255, 246, 219),
        "restaurant",
    ),
    Scene(
        29,
        41,
        "Gdańsk i praca z klientami",
        "WSB Merito, piekarnia, eventy, Żabka",
        "W Gdańsku zaczęłam psychologię w biznesie na WSB Merito i pracowałam z klientami w piekarni, na eventach i w Żabce.",
        (232, 244, 255),
        (236, 236, 255),
        "gdansk",
    ),
    Scene(
        41,
        51,
        "Kierunek: HR",
        "wyróżnienie Rektora i magisterka",
        "Dobra średnia przyniosła wyróżnienie Rektora. Po licencjacie wybrałam HR i magisterkę z zarządzania zasobami ludzkimi.",
        (255, 248, 229),
        (234, 248, 241),
        "award",
    ),
    Scene(
        51,
        63,
        "ESN Gdańsk",
        "rekrutacje i wyjazd szkoleniowy",
        "W ESN Gdańsk działałam w sekcji HR: prowadziłam rekrutacje i współorganizowałam wyjazd szkoleniowo-integracyjny.",
        (238, 243, 255),
        (255, 239, 236),
        "esn",
    ),
    Scene(
        63,
        72,
        "Erasmus w Porto",
        "międzynarodowe środowisko",
        "Teraz przygotowuję się do Erasmusa w Porto, żeby rozwijać się w międzynarodowym środowisku.",
        (225, 247, 255),
        (255, 244, 224),
        "porto",
    ),
    Scene(
        72,
        81,
        "Po godzinach",
        "szydełko, cierpliwość, dobre połączenia",
        "Po godzinach szydełkuję. Lubię patrzeć, jak z jednej nitki powstaje coś konkretnego - trochę jak w HR.",
        (254, 240, 247),
        (242, 248, 232),
        "crochet",
    ),
    Scene(
        81,
        90,
        "Szukam pierwszej pracy w HR",
        "otwarta • zorganizowana • gotowa na wyzwania",
        "Jestem otwarta, dobrze zorganizowana i gotowa na nowe wyzwania. Chętnie dołączę do międzynarodowego zespołu HR.",
        (248, 246, 255),
        (231, 248, 255),
        "final",
    ),
]


PALETTE = {
    "ink": (39, 47, 71),
    "muted": (94, 105, 130),
    "white": (255, 255, 255),
    "coral": (242, 112, 97),
    "orange": (250, 166, 71),
    "yellow": (255, 207, 96),
    "mint": (80, 196, 164),
    "teal": (54, 167, 190),
    "blue": (78, 137, 255),
    "navy": (41, 65, 121),
    "purple": (142, 111, 255),
    "pink": (236, 132, 183),
    "green": (88, 176, 104),
}


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def smoothstep(value: float) -> float:
    x = clamp(value)
    return x * x * (3 - 2 * x)


def smootherstep(value: float) -> float:
    x = clamp(value)
    return x * x * x * (x * (x * 6 - 15) + 10)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def mix(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


def find_font(name: str) -> str | None:
    candidates = [
        f"/usr/share/fonts/truetype/noto/{name}",
        f"/usr/share/fonts/truetype/dejavu/{name}",
        f"/usr/share/fonts/opentype/noto/{name}",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate

    if shutil.which("fc-match"):
        try:
            resolved = subprocess.check_output(
                ["fc-match", "-f", "%{file}", name],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            if resolved and Path(resolved).exists():
                return resolved
        except subprocess.SubprocessError:
            pass
    return None


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = [
        "NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for name in names:
        path = find_font(name)
        if path:
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default(size=size)


FONTS = {
    "title": load_font(48, bold=True),
    "subtitle": load_font(25, bold=True),
    "caption": load_font(30),
    "caption_bold": load_font(30, bold=True),
    "label": load_font(22, bold=True),
    "small": load_font(18),
    "tiny": load_font(15, bold=True),
    "giant": load_font(96, bold=True),
}


def make_gradient(top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        draw.line([(0, y), (WIDTH, y)], fill=mix(top, bottom, y / (HEIGHT - 1)) + (255,))
    return img


BG_CACHE = {(scene.bg_top, scene.bg_bottom): make_gradient(scene.bg_top, scene.bg_bottom) for scene in SCENES}


def rounded_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[float, float, float, float],
    fill: tuple[int, int, int, int] = (255, 255, 255, 230),
    radius: int = 32,
    outline: tuple[int, int, int, int] | None = None,
) -> None:
    x1, y1, x2, y2 = box
    shadow = (x1 + 8, y1 + 10, x2 + 8, y2 + 10)
    draw.rounded_rectangle(shadow, radius=radius, fill=(39, 47, 71, 24))
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2 if outline else 1)


def scene_index(scene: Scene) -> int:
    return SCENES.index(scene)


def staged(local: float, start: float, end: float) -> float:
    return smootherstep((local - start) / (end - start))


def float_offset(frame: int, amount: float, phase: float = 0.0) -> tuple[float, float]:
    return (
        math.sin(frame / 41 + phase) * amount,
        math.cos(frame / 47 + phase * 1.7) * amount,
    )


def shifted_box(box: tuple[float, float, float, float], dx: float, dy: float) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = box
    return x1 + dx, y1 + dy, x2 + dx, y2 + dy


def draw_partial_line(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[float, float]],
    progress: float,
    fill: tuple[int, int, int, int],
    width: int,
    joint: str | None = "curve",
) -> tuple[float, float]:
    """Draw a polyline only up to progress and return the current pen position."""
    progress = clamp(progress)
    if len(points) < 2:
        return points[0] if points else (0, 0)

    lengths: list[float] = []
    total = 0.0
    for a, b in zip(points, points[1:]):
        segment = math.dist(a, b)
        lengths.append(segment)
        total += segment
    target = total * progress

    drawn: list[tuple[float, float]] = [points[0]]
    travelled = 0.0
    pen = points[0]
    for index, segment in enumerate(lengths):
        a = points[index]
        b = points[index + 1]
        if travelled + segment <= target:
            drawn.append(b)
            pen = b
            travelled += segment
            continue

        part = 0 if segment == 0 else (target - travelled) / segment
        pen = (lerp(a[0], b[0], part), lerp(a[1], b[1], part))
        drawn.append(pen)
        break

    if len(drawn) > 1:
        draw.line(drawn, fill=fill, width=width, joint=joint)
    return pen


def draw_sketch_line(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[float, float]],
    progress: float,
    color: tuple[int, int, int] = PALETTE["ink"],
    width: int = 5,
    frame: int = 0,
    alpha: int = 190,
) -> tuple[float, float]:
    pen = points[0]
    for pass_index, offset in enumerate((-2.0, 1.4)):
        wobbled = [
            (
                x + math.sin(frame / 17 + i * 1.8 + pass_index) * 1.6 + offset,
                y + math.cos(frame / 19 + i * 1.4 + pass_index) * 1.4 - offset * 0.4,
            )
            for i, (x, y) in enumerate(points)
        ]
        pen = draw_partial_line(draw, wobbled, progress, color + (alpha,), max(1, width - pass_index))
    return pen


def draw_pencil(draw: ImageDraw.ImageDraw, x: float, y: float, angle: float, scale: float = 1.0) -> None:
    length = 54 * scale
    width = 15 * scale
    ux, uy = math.cos(angle), math.sin(angle)
    vx, vy = -uy, ux
    tail = (x - ux * length, y - uy * length)
    body = [
        (x - vx * width / 2, y - vy * width / 2),
        (tail[0] - vx * width / 2, tail[1] - vy * width / 2),
        (tail[0] + vx * width / 2, tail[1] + vy * width / 2),
        (x + vx * width / 2, y + vy * width / 2),
    ]
    tip = [(x + ux * 14 * scale, y + uy * 14 * scale), body[0], body[-1]]
    draw.polygon(body, fill=PALETTE["yellow"] + (245,), outline=PALETTE["ink"] + (220,))
    draw.polygon(tip, fill=(226, 187, 138, 255), outline=PALETTE["ink"] + (220,))
    draw.line((tail[0] - vx * width / 2, tail[1] - vy * width / 2, tail[0] + vx * width / 2, tail[1] + vy * width / 2), fill=PALETTE["coral"] + (255,), width=max(2, int(4 * scale)))


def draw_paper_texture(draw: ImageDraw.ImageDraw, frame: int) -> None:
    for i in range(34):
        x = (i * 97 + 31) % WIDTH
        y = (i * 53 + 71) % HEIGHT
        drift = math.sin(frame / 90 + i) * 2
        draw.line((x - 18, y + drift, x + 18, y + drift + 1), fill=(39, 47, 71, 10), width=1)


def draw_scene_doodles(draw: ImageDraw.ImageDraw, scene: Scene, local: float, frame: int) -> None:
    progress = staged(local, 0.05, 0.46)
    underline = [(86, 151), (190, 146), (310, 153), (430, 149), (535, 154)]
    pen = draw_sketch_line(draw, underline, progress, PALETTE["coral"], 6, frame, 210)

    card_path = [
        (328, 178),
        (950, 172),
        (1018, 250),
        (965, 506),
        (320, 512),
        (250, 430),
        (296, 190),
    ]
    card_progress = staged(local, 0.16, 0.66)
    pen = draw_sketch_line(draw, card_path, card_progress, PALETTE["navy"], 4, frame, 90)

    scene_paths = {
        "intro": [(560, 462), (620, 430), (690, 455), (746, 420), (780, 454)],
        "twins": [(410, 443), (520, 410), (640, 452), (760, 410), (875, 443)],
        "restaurant": [(440, 454), (540, 425), (675, 452), (805, 420), (900, 455)],
        "gdansk": [(338, 482), (480, 448), (640, 482), (800, 448), (950, 482)],
        "award": [(402, 474), (545, 444), (665, 474), (795, 444), (910, 474)],
        "esn": [(336, 468), (500, 438), (660, 470), (805, 438), (930, 470)],
        "porto": [(410, 382), (540, 270), (700, 248), (835, 335), (910, 292)],
        "crochet": [(465, 335), (610, 248), (805, 252), (900, 360), (755, 440), (640, 375)],
        "final": [(395, 452), (530, 420), (650, 452), (782, 420), (900, 452)],
    }
    path = scene_paths.get(scene.icon, underline)
    animated = staged(local, 0.26, 0.82)
    pen = draw_sketch_line(draw, path, animated, PALETTE["teal"], 5, frame, 175)

    if 0.05 < local < 0.86:
        next_point = path[min(len(path) - 1, max(1, int(animated * (len(path) - 1))))]
        angle = math.atan2(next_point[1] - pen[1], next_point[0] - pen[0])
        draw_pencil(draw, pen[0], pen[1], angle, 0.72)


def apply_camera_motion(img: Image.Image, scene: Scene, local: float, frame: int) -> Image.Image:
    zoom = 1.0 + 0.012 * math.sin(frame / 130 + scene_index(scene) * 0.7)
    pan_x = math.sin(frame / 96 + scene_index(scene)) * 10
    pan_y = math.cos(frame / 111 + scene_index(scene) * 0.8) * 7
    scaled_w = int(WIDTH * zoom)
    scaled_h = int(HEIGHT * zoom)
    resized = img.resize((scaled_w, scaled_h), Image.Resampling.BICUBIC)
    left = int((scaled_w - WIDTH) / 2 + pan_x)
    top = int((scaled_h - HEIGHT) / 2 + pan_y)
    left = max(0, min(left, scaled_w - WIDTH))
    top = max(0, min(top, scaled_h - HEIGHT))
    return resized.crop((left, top, left + WIDTH, top + HEIGHT))


def slide_blend(previous: Image.Image, current: Image.Image, alpha: float) -> Image.Image:
    alpha = smootherstep(alpha)
    shifted = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 0))
    offset = int((1 - alpha) * 155)
    shifted.alpha_composite(current.convert("RGBA"), (offset, 0))
    mask = Image.new("L", (WIDTH, HEIGHT), int(alpha * 255))
    blended = Image.composite(shifted, previous.convert("RGBA"), mask)
    wipe = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    wipe_draw = ImageDraw.Draw(wipe)
    x = int(lerp(-260, WIDTH + 260, alpha))
    wipe_draw.polygon([(x - 120, 0), (x + 20, 0), (x - 120, HEIGHT), (x - 260, HEIGHT)], fill=PALETTE["coral"] + (70,))
    blended.alpha_composite(wipe)
    return blended


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def wrap_lines(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        attempt = f"{current} {word}".strip()
        if draw.textlength(attempt, font=font) <= max_width:
            current = attempt
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_centered_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    center_x: float,
    top: float,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int] | tuple[int, int, int, int],
    line_gap: int = 8,
) -> None:
    y = top
    for line in lines:
        w, h = text_size(draw, line, font)
        draw.text((center_x - w / 2, y), line, font=font, fill=fill)
        y += h + line_gap


def draw_header(draw: ImageDraw.ImageDraw, scene: Scene, t: float, local: float) -> None:
    x = lerp(-560, 70, smoothstep(local * 2.8))
    draw.rounded_rectangle((70, 34, WIDTH - 70, 44), radius=5, fill=(255, 255, 255, 130))
    draw.rounded_rectangle((70, 34, 70 + (WIDTH - 140) * (t / DURATION), 44), radius=5, fill=PALETTE["coral"] + (220,))
    draw.rounded_rectangle((x, 70, x + 18, 136), radius=9, fill=PALETTE["coral"] + (255,))
    draw.text((x + 34, 66), scene.title, font=FONTS["title"], fill=PALETTE["ink"])
    draw.text((x + 36, 123), scene.kicker, font=FONTS["subtitle"], fill=PALETTE["muted"])


def draw_caption(img: Image.Image, scene: Scene, local: float) -> None:
    draw = ImageDraw.Draw(img)
    alpha = int(235 * smoothstep(local * 2.0))
    card = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card)
    box = (95, 560, WIDTH - 95, 675)
    rounded_card(card_draw, box, fill=(255, 255, 255, alpha), radius=28)
    img.alpha_composite(card)
    draw = ImageDraw.Draw(img)
    lines = wrap_lines(draw, scene.caption, FONTS["caption"], WIDTH - 260)
    draw_centered_lines(draw, lines[:3], WIDTH / 2, 590, FONTS["caption"], PALETTE["ink"], line_gap=6)


def draw_person(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    scale: float = 1.0,
    shirt: tuple[int, int, int] = PALETTE["blue"],
    hair: tuple[int, int, int] = (95, 61, 48),
    wave: float = 0.0,
) -> None:
    s = scale
    draw.rounded_rectangle((x - 42 * s, y + 28 * s, x + 42 * s, y + 112 * s), radius=int(22 * s), fill=shirt + (255,))
    draw.pieslice((x - 45 * s, y - 35 * s, x + 45 * s, y + 55 * s), 180, 360, fill=hair + (255,))
    draw.ellipse((x - 38 * s, y - 24 * s, x + 38 * s, y + 52 * s), fill=(255, 214, 185, 255))
    draw.arc((x - 24 * s, y - 26 * s, x + 24 * s, y + 34 * s), 190, 350, fill=hair + (255,), width=max(1, int(8 * s)))
    eye_r = 3.4 * s
    draw.ellipse((x - 16 * s - eye_r, y + 9 * s - eye_r, x - 16 * s + eye_r, y + 9 * s + eye_r), fill=PALETTE["ink"] + (255,))
    draw.ellipse((x + 16 * s - eye_r, y + 9 * s - eye_r, x + 16 * s + eye_r, y + 9 * s + eye_r), fill=PALETTE["ink"] + (255,))
    draw.arc((x - 16 * s, y + 17 * s, x + 16 * s, y + 34 * s), 10, 170, fill=PALETTE["ink"] + (255,), width=max(1, int(2 * s)))
    arm_angle = math.sin(wave) * 10
    draw.line((x - 40 * s, y + 58 * s, x - 76 * s, y + (72 - arm_angle) * s), fill=shirt + (255,), width=max(2, int(11 * s)))
    draw.line((x + 40 * s, y + 58 * s, x + 75 * s, y + (70 + arm_angle) * s), fill=shirt + (255,), width=max(2, int(11 * s)))


def draw_label(draw: ImageDraw.ImageDraw, text: str, x: float, y: float, color: tuple[int, int, int]) -> None:
    w, h = text_size(draw, text, FONTS["label"])
    draw.rounded_rectangle((x - w / 2 - 16, y - 8, x + w / 2 + 16, y + h + 10), radius=16, fill=color + (225,))
    draw.text((x - w / 2, y), text, font=FONTS["label"], fill=PALETTE["white"])


def draw_city(draw: ImageDraw.ImageDraw, base_y: float, offset: float = 0.0) -> None:
    colors = [PALETTE["navy"], PALETTE["blue"], PALETTE["teal"], PALETTE["purple"]]
    xs = [180, 250, 330, 405, 790, 880, 975, 1060]
    heights = [115, 80, 135, 95, 90, 130, 75, 115]
    for i, (x, h) in enumerate(zip(xs, heights)):
        y = base_y - h + math.sin(offset + i) * 5
        draw.rounded_rectangle((x, y, x + 58, base_y), radius=12, fill=colors[i % len(colors)] + (170,))
        for wy in range(int(y + 18), int(base_y - 10), 24):
            draw.rectangle((x + 17, wy, x + 27, wy + 9), fill=(255, 255, 255, 120))
            draw.rectangle((x + 35, wy, x + 45, wy + 9), fill=(255, 255, 255, 120))


def icon_intro(draw: ImageDraw.ImageDraw, local: float, frame: int) -> None:
    rounded_card(draw, (345, 175, 935, 500), fill=(255, 255, 255, 220), radius=40)
    draw_city(draw, 490, frame / 25)
    pin_y = lerp(120, 250, smoothstep(local * 2.5))
    draw.polygon([(640, pin_y + 78), (602, pin_y + 16), (678, pin_y + 16)], fill=PALETTE["coral"] + (255,))
    draw.ellipse((590, pin_y - 40, 690, pin_y + 60), fill=PALETTE["coral"] + (255,))
    draw.ellipse((622, pin_y - 8, 658, pin_y + 28), fill=PALETTE["white"] + (255,))
    draw_person(draw, 640, 310, 1.05, shirt=PALETTE["blue"], wave=frame / 7)
    draw_label(draw, "OLSZTYN", 640, 464, PALETTE["navy"])


def icon_twins(draw: ImageDraw.ImageDraw, local: float, frame: int) -> None:
    rounded_card(draw, (290, 185, 990, 492), fill=(255, 255, 255, 220), radius=40)
    spread = lerp(70, 190, smoothstep(local * 2.0))
    draw_person(draw, 640 - spread, 280, 0.95, shirt=PALETTE["purple"], wave=frame / 8)
    draw_person(draw, 640 + spread, 280, 0.95, shirt=PALETTE["pink"], wave=frame / 8 + 1.5)
    for cx, text, color in [
        (438, "win-win", PALETTE["mint"]),
        (842, "współpraca", PALETTE["blue"]),
    ]:
        draw.rounded_rectangle((cx - 88, 205, cx + 88, 248), radius=20, fill=color + (230,))
        w, _ = text_size(draw, text, FONTS["label"])
        draw.text((cx - w / 2, 214), text, font=FONTS["label"], fill=PALETTE["white"])
    cake_x = 640
    draw.polygon([(cake_x - 48, 435), (cake_x + 52, 435), (cake_x - 8, 385)], fill=PALETTE["yellow"] + (255,))
    draw.polygon([(cake_x - 48, 435), (cake_x + 52, 435), (cake_x + 22, 455), (cake_x - 70, 455)], fill=PALETTE["orange"] + (255,))
    draw.arc((cake_x - 54, 382, cake_x + 56, 455), 210, 335, fill=PALETTE["coral"] + (255,), width=5)


def icon_restaurant(draw: ImageDraw.ImageDraw, local: float, frame: int) -> None:
    rounded_card(draw, (335, 185, 945, 500), fill=(255, 255, 255, 220), radius=40)
    tray_x = lerp(420, 670, smoothstep(local))
    draw.ellipse((tray_x - 155, 390, tray_x + 155, 435), fill=(186, 196, 215, 255))
    draw.rounded_rectangle((tray_x - 185, 426, tray_x + 185, 448), radius=11, fill=PALETTE["navy"] + (255,))
    draw.ellipse((tray_x - 82, 300, tray_x + 82, 418), fill=PALETTE["white"] + (255,), outline=PALETTE["navy"] + (255,), width=5)
    draw.ellipse((tray_x - 43, 325, tray_x + 43, 389), fill=PALETTE["mint"] + (255,))
    clock_x, clock_y = 825, 315
    draw.ellipse((clock_x - 62, clock_y - 62, clock_x + 62, clock_y + 62), fill=PALETTE["yellow"] + (255,), outline=PALETTE["ink"] + (255,), width=5)
    angle = frame / 8
    draw.line((clock_x, clock_y, clock_x + math.cos(angle) * 34, clock_y + math.sin(angle) * 34), fill=PALETTE["ink"] + (255,), width=5)
    draw.line((clock_x, clock_y, clock_x, clock_y - 42), fill=PALETTE["ink"] + (255,), width=4)
    for i, text in enumerate(["tempo", "kontakt", "organizacja"]):
        y = 246 + i * 49
        draw.rounded_rectangle((420, y, 575, y + 34), radius=14, fill=(255, 255, 255, 245), outline=PALETTE["mint"] + (255,), width=2)
        draw.text((450, y + 5), text, font=FONTS["small"], fill=PALETTE["ink"])
        draw.line((431, y + 16, 439, y + 25, 454, y + 6), fill=PALETTE["green"] + (255,), width=4)


def icon_gdansk(draw: ImageDraw.ImageDraw, local: float, frame: int) -> None:
    rounded_card(draw, (250, 178, 1030, 506), fill=(255, 255, 255, 220), radius=40)
    draw_city(draw, 502, frame / 34)
    draw.rounded_rectangle((502, 235, 778, 390), radius=18, fill=PALETTE["blue"] + (235,))
    draw.polygon([(490, 235), (640, 155), (790, 235)], fill=PALETTE["navy"] + (245,))
    draw.rectangle((617, 300, 663, 390), fill=(255, 255, 255, 180))
    draw.text((560, 246), "WSB", font=FONTS["title"], fill=PALETTE["white"])
    draw.text((547, 310), "Merito", font=FONTS["label"], fill=PALETTE["white"])
    cards = [
        ("piekarnia", PALETTE["orange"], 380),
        ("eventy", PALETTE["purple"], 640),
        ("Żabka", PALETTE["green"], 900),
    ]
    for i, (label, color, x) in enumerate(cards):
        lift = math.sin(frame / 12 + i) * 7
        draw.rounded_rectangle((x - 86, 410 + lift, x + 86, 476 + lift), radius=24, fill=color + (245,))
        w, _ = text_size(draw, label, FONTS["label"])
        draw.text((x - w / 2, 431 + lift), label, font=FONTS["label"], fill=PALETTE["white"])


def icon_award(draw: ImageDraw.ImageDraw, local: float, frame: int) -> None:
    rounded_card(draw, (330, 170, 950, 508), fill=(255, 255, 255, 224), radius=40)
    draw.rounded_rectangle((420, 235, 615, 445), radius=18, fill=(255, 255, 255, 255), outline=PALETTE["navy"] + (255,), width=4)
    draw.text((455, 258), "Dyplom", font=FONTS["subtitle"], fill=PALETTE["navy"])
    for y in [312, 346, 380]:
        draw.line((455, y, 580, y), fill=PALETTE["muted"] + (180,), width=4)
    draw.polygon([(575, 215), (600, 265), (655, 273), (616, 312), (625, 366), (575, 340), (525, 366), (534, 312), (495, 273), (550, 265)], fill=PALETTE["yellow"] + (255,))
    draw.ellipse((525, 260, 625, 360), fill=PALETTE["orange"] + (255,), outline=PALETTE["ink"] + (255,), width=4)
    draw.text((552, 287), "5", font=FONTS["title"], fill=PALETTE["white"])
    draw.rounded_rectangle((690, 238, 858, 435), radius=26, fill=PALETTE["purple"] + (245,))
    draw.text((717, 276), "HR", font=FONTS["giant"], fill=PALETTE["white"])
    draw_label(draw, "Uniwersytet Gdański", 640, 468, PALETTE["teal"])


def icon_esn(draw: ImageDraw.ImageDraw, local: float, frame: int) -> None:
    rounded_card(draw, (265, 170, 1015, 508), fill=(255, 255, 255, 224), radius=40)
    funnel = [(385, 235), (575, 235), (530, 350), (495, 350), (495, 430), (455, 430), (455, 350)]
    draw.polygon(funnel, fill=PALETTE["blue"] + (230,))
    draw.text((409, 253), "rekrutacja", font=FONTS["label"], fill=PALETTE["white"])
    for i in range(4):
        x = 640 + i * 68
        y = 235 + math.sin(frame / 10 + i) * 8
        draw.rounded_rectangle((x, y, x + 48, y + 64), radius=12, fill=(255, 255, 255, 255), outline=PALETTE["purple"] + (255,), width=3)
        draw.ellipse((x + 14, y + 10, x + 34, y + 30), fill=PALETTE["yellow"] + (255,))
        draw.line((x + 12, y + 43, x + 36, y + 43), fill=PALETTE["muted"] + (255,), width=3)
    draw.rounded_rectangle((678, 370, 900, 438), radius=22, fill=PALETTE["coral"] + (245,))
    draw.ellipse((700, 424, 735, 459), fill=PALETTE["ink"] + (255,))
    draw.ellipse((840, 424, 875, 459), fill=PALETTE["ink"] + (255,))
    draw.text((721, 390), "wyjazd", font=FONTS["label"], fill=PALETTE["white"])
    for x, y in [(340, 430), (500, 455), (700, 330), (910, 310)]:
        draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=PALETTE["mint"] + (255,))
    draw.line((350, 430, 500, 455, 700, 330, 910, 310), fill=PALETTE["mint"] + (210,), width=4, joint="curve")


def icon_porto(draw: ImageDraw.ImageDraw, local: float, frame: int) -> None:
    rounded_card(draw, (285, 175, 995, 505), fill=(255, 255, 255, 224), radius=40)
    draw.ellipse((830, 215, 910, 295), fill=PALETTE["yellow"] + (255,))
    for i in range(5):
        y = 390 + i * 18 + math.sin(frame / 12 + i) * 4
        draw.arc((335, y, 945, y + 70), 0, 180, fill=PALETTE["teal"] + (145,), width=4)
    start = (430, 335)
    end = (830, 290)
    for i in range(18):
        p = i / 17
        x = lerp(start[0], end[0], p)
        y = lerp(start[1], end[1], p) - math.sin(p * math.pi) * 90
        if i % 2 == 0:
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=PALETTE["blue"] + (180,))
    p = smoothstep(local)
    px = lerp(start[0], end[0], p)
    py = lerp(start[1], end[1], p) - math.sin(p * math.pi) * 90
    draw.polygon([(px + 38, py), (px - 28, py - 18), (px - 15, py), (px - 28, py + 18)], fill=PALETTE["navy"] + (255,))
    draw.polygon([(px - 8, py), (px - 42, py - 38), (px - 22, py), (px - 42, py + 38)], fill=PALETTE["blue"] + (255,))
    draw_label(draw, "Gdańsk", start[0], start[1] + 45, PALETTE["blue"])
    draw_label(draw, "Porto", end[0], end[1] + 45, PALETTE["coral"])


def icon_crochet(draw: ImageDraw.ImageDraw, local: float, frame: int) -> None:
    rounded_card(draw, (295, 170, 985, 505), fill=(255, 255, 255, 224), radius=40)
    center = (465, 335)
    for r in range(92, 10, -13):
        draw.ellipse((center[0] - r, center[1] - r, center[0] + r, center[1] + r), outline=PALETTE["pink"] + (245,), width=7)
    for i in range(8):
        angle = frame / 30 + i * math.pi / 4
        draw.arc((center[0] - 96, center[1] - 96, center[0] + 96, center[1] + 96), math.degrees(angle), math.degrees(angle) + 80, fill=PALETTE["purple"] + (180,), width=5)
    points = [(655, 255), (815, 250), (890, 360), (755, 440), (640, 375)]
    thread_end = int(lerp(0, len(points), smoothstep(local)))
    path = [center] + points[: max(1, thread_end)]
    draw.line(path, fill=PALETTE["pink"] + (255,), width=6, joint="curve")
    for i, (x, y) in enumerate(points):
        if local > i / len(points) * 0.7:
            draw.ellipse((x - 24, y - 24, x + 24, y + 24), fill=PALETTE["mint"] + (255,), outline=PALETTE["ink"] + (255,), width=3)
            label = ["cierpliwość", "pomysł", "kontakt", "zespół", "HR"][i]
            w, _ = text_size(draw, label, FONTS["tiny"])
            draw.text((x - w / 2, y + 31), label, font=FONTS["tiny"], fill=PALETTE["ink"])


def icon_final(draw: ImageDraw.ImageDraw, local: float, frame: int) -> None:
    rounded_card(draw, (260, 162, 1020, 512), fill=(255, 255, 255, 228), radius=42)
    draw_person(draw, 445, 280, 1.12, shirt=PALETTE["blue"], wave=frame / 6)
    draw.rounded_rectangle((585, 230, 880, 430), radius=32, fill=PALETTE["navy"] + (245,))
    draw.text((647, 258), "HR", font=FONTS["giant"], fill=PALETTE["white"])
    strengths = [("otwarta", PALETTE["mint"]), ("zorganizowana", PALETTE["purple"]), ("gotowa na wyzwania", PALETTE["coral"])]
    for i, (label, color) in enumerate(strengths):
        y = 452 + i * 0
        x = 430 + i * 220
        pop = smoothstep(local * 2.0 - i * 0.18)
        draw.rounded_rectangle((x - 88, y - 30 * pop, x + 88, y + 25 * pop), radius=20, fill=color + (240,))
        if pop > 0.2:
            w, _ = text_size(draw, label, FONTS["label"])
            draw.text((x - w / 2, y - 15), label, font=FONTS["label"], fill=PALETTE["white"])


ICON_DRAWERS = {
    "intro": icon_intro,
    "twins": icon_twins,
    "restaurant": icon_restaurant,
    "gdansk": icon_gdansk,
    "award": icon_award,
    "esn": icon_esn,
    "porto": icon_porto,
    "crochet": icon_crochet,
    "final": icon_final,
}


WHITEBOARD_STYLE = True


def wb_color(name: str, alpha: int = 255) -> tuple[int, int, int, int]:
    return PALETTE[name] + (alpha,)


def draw_wb_background(draw: ImageDraw.ImageDraw, frame: int) -> None:
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(252, 250, 244, 255))
    for y in range(86, HEIGHT, 86):
        draw.line((0, y, WIDTH, y + math.sin(frame / 80 + y) * 2), fill=(42, 50, 70, 13), width=1)
    for x in range(95, WIDTH, 95):
        draw.line((x, 0, x + math.sin(frame / 90 + x) * 2, HEIGHT), fill=(42, 50, 70, 8), width=1)
    for i in range(42):
        x = (i * 143 + 37) % WIDTH
        y = (i * 79 + 53) % HEIGHT
        draw.ellipse((x, y, x + 2, y + 2), fill=(42, 50, 70, 20))


def wb_reveal(local: float, index: int, total: int, span: float = 0.55) -> float:
    start = 0.06 + index * (span / max(1, total))
    end = start + span / max(2, total) * 1.6
    return smootherstep((local - start) / (end - start))


def draw_wb_partial_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[float, float],
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    progress: float,
) -> None:
    amount = int(len(text) * clamp(progress))
    if amount > 0:
        draw.text(xy, text[:amount], font=font, fill=fill)


def draw_wb_header(draw: ImageDraw.ImageDraw, scene: Scene, t: float, local: float, frame: int) -> None:
    progress = smootherstep(local * 5.0)
    title = scene.title
    kicker = scene.kicker
    draw_wb_partial_text(draw, title, (78, 58), FONTS["title"], PALETTE["ink"], progress)
    draw_wb_partial_text(draw, kicker, (82, 116), FONTS["subtitle"], PALETTE["muted"], smootherstep(local * 8.0 - 0.7))

    underline = [(82, 157), (170, 153), (265, 158), (360, 154), (478, 158), (560, 154)]
    pen = draw_sketch_line(draw, underline, smootherstep(local * 2.0 - 0.18), PALETTE["coral"], 5, frame, 225)
    if 0.10 < local < 0.58:
        draw_marker_hand(draw, pen[0], pen[1], -0.06 + math.sin(frame / 18) * 0.06, 0.78)

    draw.rounded_rectangle((775, 68, 1194, 106), radius=20, outline=wb_color("muted", 80), width=2)
    draw.rounded_rectangle((775, 68, 775 + 419 * (t / DURATION), 106), radius=20, fill=wb_color("teal", 120))
    draw.text((795, 75), f"{int(t):02d}s / 90s", font=FONTS["small"], fill=PALETTE["ink"])


def draw_wb_caption(draw: ImageDraw.ImageDraw, scene: Scene, local: float, frame: int) -> None:
    box = (92, 558, 1188, 668)
    progress = smootherstep(local * 4.0 - 0.2)
    outline = [(box[0], box[1]), (box[2], box[1] + 3), (box[2] - 5, box[3]), (box[0] + 4, box[3]), (box[0], box[1])]
    draw.rounded_rectangle(box, radius=24, fill=(255, 255, 255, int(214 * progress)))
    draw_sketch_line(draw, outline, progress, PALETTE["ink"], 3, frame, 130)
    lines = wrap_lines(draw, scene.caption, FONTS["caption"], WIDTH - 250)
    y = 590
    text_progress = smootherstep(local * 8.0 - 0.7)
    for line in lines[:3]:
        w, h = text_size(draw, line, FONTS["caption"])
        draw_wb_partial_text(draw, line, (WIDTH / 2 - w / 2, y), FONTS["caption"], PALETTE["ink"], text_progress)
        y += h + 7


def draw_marker_hand(draw: ImageDraw.ImageDraw, x: float, y: float, angle: float, scale: float = 1.0) -> None:
    ux, uy = math.cos(angle), math.sin(angle)
    vx, vy = -uy, ux
    length = 74 * scale
    width = 20 * scale
    tail = (x - ux * length, y - uy * length)
    body = [
        (x - vx * width / 2, y - vy * width / 2),
        (tail[0] - vx * width / 2, tail[1] - vy * width / 2),
        (tail[0] + vx * width / 2, tail[1] + vy * width / 2),
        (x + vx * width / 2, y + vy * width / 2),
    ]
    draw.polygon(body, fill=(245, 245, 240, 255), outline=wb_color("ink", 230))
    draw.line((tail[0] - vx * width / 2, tail[1] - vy * width / 2, tail[0] + vx * width / 2, tail[1] + vy * width / 2), fill=wb_color("coral"), width=max(2, int(6 * scale)))
    draw.ellipse((tail[0] - 32 * scale, tail[1] - 18 * scale, tail[0] + 18 * scale, tail[1] + 27 * scale), fill=(255, 214, 185, 245), outline=wb_color("ink", 160), width=2)


def draw_wb_arc(
    draw: ImageDraw.ImageDraw,
    box: tuple[float, float, float, float],
    start: float,
    end: float,
    progress: float,
    color: tuple[int, int, int] = PALETTE["ink"],
    width: int = 4,
    frame: int = 0,
) -> None:
    angle = start + (end - start) * clamp(progress)
    for offset in (-1.0, 1.0):
        wobble = math.sin(frame / 18 + box[0]) * 1.1
        shifted = (box[0] + offset, box[1] + wobble, box[2] + offset, box[3] + wobble)
        draw.arc(shifted, start, angle, fill=color + (205,), width=width)


def draw_wb_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[float, float, float, float],
    progress: float,
    color: tuple[int, int, int] = PALETTE["ink"],
    width: int = 4,
    frame: int = 0,
) -> None:
    x1, y1, x2, y2 = box
    points = [(x1, y1), (x2, y1 + 3), (x2 - 5, y2), (x1 + 3, y2), (x1, y1)]
    draw_sketch_line(draw, points, progress, color, width, frame, 210)


def draw_wb_person(draw: ImageDraw.ImageDraw, x: float, y: float, scale: float, progress: float, frame: int, accent: str = "blue") -> None:
    s = scale
    p1 = clamp(progress * 1.3)
    body = [(x, y + 48 * s), (x, y + 122 * s), (x - 45 * s, y + 180 * s), (x, y + 122 * s), (x + 45 * s, y + 180 * s)]
    draw_sketch_line(draw, body, p1, PALETTE["ink"], max(2, int(4 * s)), frame, 210)
    draw_wb_arc(draw, (x - 38 * s, y - 26 * s, x + 38 * s, y + 50 * s), 0, 360, p1, PALETTE["ink"], max(2, int(4 * s)), frame)
    hair = [(x - 38 * s, y + 8 * s), (x - 18 * s, y - 28 * s), (x + 16 * s, y - 22 * s), (x + 38 * s, y + 5 * s)]
    draw_sketch_line(draw, hair, clamp(progress * 1.5 - 0.15), (95, 61, 48), max(2, int(4 * s)), frame, 220)
    arm = math.sin(frame / 8) * 8
    draw_sketch_line(draw, [(x, y + 80 * s), (x - 72 * s, y + (95 - arm) * s)], clamp(progress * 1.4 - 0.05), PALETTE[accent], max(3, int(5 * s)), frame, 230)
    draw_sketch_line(draw, [(x, y + 80 * s), (x + 72 * s, y + (95 + arm) * s)], clamp(progress * 1.4 - 0.08), PALETTE[accent], max(3, int(5 * s)), frame, 230)
    if progress > 0.68:
        draw.ellipse((x - 15 * s, y + 5 * s, x - 9 * s, y + 11 * s), fill=wb_color("ink"))
        draw.ellipse((x + 9 * s, y + 5 * s, x + 15 * s, y + 11 * s), fill=wb_color("ink"))
        draw.arc((x - 16 * s, y + 14 * s, x + 16 * s, y + 33 * s), 8, 172, fill=wb_color("ink"), width=max(1, int(2 * s)))


def wb_keyword(draw: ImageDraw.ImageDraw, text: str, x: float, y: float, progress: float, color: str, frame: int) -> None:
    if progress <= 0:
        return
    w, h = text_size(draw, text, FONTS["label"])
    box = (x - w / 2 - 18, y - 9, x + w / 2 + 18, y + h + 10)
    draw_wb_box(draw, box, progress, PALETTE[color], 3, frame)
    if progress > 0.45:
        draw.text((x - w / 2, y), text, font=FONTS["label"], fill=PALETTE["ink"])


def wb_intro(draw: ImageDraw.ImageDraw, local: float, frame: int) -> None:
    p = wb_reveal(local, 0, 5)
    draw_wb_person(draw, 640, 248, 1.08, p, frame, "blue")
    draw_wb_arc(draw, (565, 188, 715, 338), 220, 500, wb_reveal(local, 1, 5), PALETTE["coral"], 6, frame)
    draw_sketch_line(draw, [(640, 340), (620, 388), (640, 430), (660, 388), (640, 340)], wb_reveal(local, 1, 5), PALETTE["coral"], 5, frame, 220)
    for i, (x, h) in enumerate([(385, 88), (455, 128), (520, 74), (815, 114), (890, 82)]):
        pr = wb_reveal(local, i + 2, 7)
        draw_wb_box(draw, (x, 420 - h, x + 42, 420), pr, PALETTE["ink"], 3, frame)
        if pr > 0.6:
            draw.line((x + 12, 420 - h + 24, x + 30, 420 - h + 24), fill=wb_color("blue", 170), width=4)
    wb_keyword(draw, "OLSZTYN", 640, 444, wb_reveal(local, 4, 5), "blue", frame)


def wb_twins(draw: ImageDraw.ImageDraw, local: float, frame: int) -> None:
    draw_wb_person(draw, 520, 255, 0.92, wb_reveal(local, 0, 5), frame, "purple")
    draw_wb_person(draw, 760, 255, 0.92, wb_reveal(local, 1, 5), frame, "pink")
    draw_sketch_line(draw, [(575, 330), (622, 350), (670, 350), (715, 330)], wb_reveal(local, 2, 5), PALETTE["mint"], 5, frame, 220)
    wb_keyword(draw, "negocjacje", 460, 430, wb_reveal(local, 2, 5), "coral", frame)
    wb_keyword(draw, "współpraca", 655, 455, wb_reveal(local, 3, 5), "teal", frame)
    wb_keyword(draw, "dzielenie", 850, 430, wb_reveal(local, 4, 5), "purple", frame)


def wb_restaurant(draw: ImageDraw.ImageDraw, local: float, frame: int) -> None:
    tray = [(430, 420), (850, 420)]
    draw_sketch_line(draw, tray, wb_reveal(local, 0, 6), PALETTE["ink"], 6, frame, 220)
    draw_wb_arc(draw, (515, 280, 685, 405), 0, 360, wb_reveal(local, 1, 6), PALETTE["ink"], 5, frame)
    draw_wb_arc(draw, (555, 315, 645, 382), 0, 360, wb_reveal(local, 2, 6), PALETTE["mint"], 5, frame)
    draw_wb_arc(draw, (745, 270, 875, 400), 0, 360, wb_reveal(local, 2, 6), PALETTE["orange"], 5, frame)
    angle = frame / 7
    if local > 0.38:
        draw.line((810, 335, 810 + math.cos(angle) * 35, 335 + math.sin(angle) * 35), fill=wb_color("ink"), width=4)
        draw.line((810, 335, 810, 296), fill=wb_color("ink"), width=3)
    for i, text in enumerate(["tempo", "kontakt", "organizacja"]):
        wb_keyword(draw, text, 438 + i * 200, 455, wb_reveal(local, i + 3, 6), ["coral", "blue", "teal"][i], frame)


def wb_gdansk(draw: ImageDraw.ImageDraw, local: float, frame: int) -> None:
    draw_sketch_line(draw, [(470, 380), (640, 260), (810, 380), (470, 380)], wb_reveal(local, 0, 6), PALETTE["ink"], 5, frame, 220)
    draw_wb_box(draw, (515, 380, 765, 455), wb_reveal(local, 1, 6), PALETTE["ink"], 4, frame)
    draw_wb_partial_text(draw, "WSB Merito", (555, 397), FONTS["subtitle"], PALETTE["ink"], wb_reveal(local, 2, 6))
    for i, (text, x, color) in enumerate([("piekarnia", 390, "orange"), ("eventy", 640, "purple"), ("Żabka", 890, "green")]):
        wb_keyword(draw, text, x, 480, wb_reveal(local, i + 3, 6), color, frame)
    draw_sketch_line(draw, [(390, 456), (515, 430), (640, 456), (765, 430), (890, 456)], wb_reveal(local, 5, 6), PALETTE["blue"], 4, frame, 190)


def wb_award(draw: ImageDraw.ImageDraw, local: float, frame: int) -> None:
    draw_wb_box(draw, (435, 245, 625, 440), wb_reveal(local, 0, 5), PALETTE["ink"], 4, frame)
    draw_wb_partial_text(draw, "Dyplom", (475, 270), FONTS["subtitle"], PALETTE["ink"], wb_reveal(local, 1, 5))
    for i, y in enumerate([325, 355, 385]):
        draw_sketch_line(draw, [(475, y), (590, y + math.sin(frame / 20 + i) * 2)], wb_reveal(local, i + 1, 6), PALETTE["muted"], 3, frame, 160)
    star = [(705, 245), (734, 306), (800, 314), (752, 358), (765, 425), (705, 392), (645, 425), (658, 358), (610, 314), (676, 306), (705, 245)]
    draw_sketch_line(draw, star, wb_reveal(local, 2, 5), PALETTE["orange"], 5, frame, 230)
    draw_wb_partial_text(draw, "HR", (790, 330), FONTS["giant"], PALETTE["purple"], wb_reveal(local, 3, 5))
    wb_keyword(draw, "wyróżnienie Rektora", 650, 470, wb_reveal(local, 4, 5), "teal", frame)


def wb_esn(draw: ImageDraw.ImageDraw, local: float, frame: int) -> None:
    funnel = [(420, 250), (620, 250), (565, 355), (535, 355), (535, 430), (505, 430), (505, 355), (420, 250)]
    draw_sketch_line(draw, funnel, wb_reveal(local, 0, 6), PALETTE["blue"], 5, frame, 220)
    draw_wb_partial_text(draw, "rekrutacje", (447, 275), FONTS["label"], PALETTE["ink"], wb_reveal(local, 1, 6))
    for i in range(4):
        x = 690 + i * 58
        y = 260 + math.sin(frame / 12 + i) * 8
        draw_wb_box(draw, (x, y, x + 43, y + 62), wb_reveal(local, i + 2, 7), PALETTE["purple"], 3, frame)
        if local > 0.35 + i * 0.06:
            draw.ellipse((x + 15, y + 12, x + 28, y + 25), outline=wb_color("ink"), width=2)
    draw_wb_box(draw, (700, 390, 930, 455), wb_reveal(local, 5, 6), PALETTE["coral"], 5, frame)
    draw_wb_partial_text(draw, "wyjazd", (760, 410), FONTS["label"], PALETTE["ink"], wb_reveal(local, 5, 6))


def wb_porto(draw: ImageDraw.ImageDraw, local: float, frame: int) -> None:
    path = [(420, 385), (540, 270), (705, 250), (860, 340)]
    draw_sketch_line(draw, path, wb_reveal(local, 0, 5), PALETTE["blue"], 4, frame, 210)
    p = wb_reveal(local, 1, 5)
    pen = draw_partial_line(draw, path, p, PALETTE["teal"] + (0,), 1)
    plane = [(pen[0] + 36, pen[1]), (pen[0] - 25, pen[1] - 20), (pen[0] - 10, pen[1]), (pen[0] - 25, pen[1] + 20)]
    draw.polygon(plane, outline=wb_color("ink"), fill=wb_color("blue", 60))
    wb_keyword(draw, "Gdańsk", 420, 430, wb_reveal(local, 2, 5), "blue", frame)
    wb_keyword(draw, "Porto", 860, 385, wb_reveal(local, 3, 5), "coral", frame)
    wb_keyword(draw, "międzynarodowo", 640, 470, wb_reveal(local, 4, 5), "teal", frame)


def wb_crochet(draw: ImageDraw.ImageDraw, local: float, frame: int) -> None:
    center = (440, 350)
    for i, r in enumerate([92, 72, 52, 32]):
        draw_wb_arc(draw, (center[0] - r, center[1] - r, center[0] + r, center[1] + r), 0, 360, wb_reveal(local, i, 7), PALETTE["pink"], 5, frame)
    thread = [(530, 350), (640, 275), (770, 275), (870, 360), (780, 455), (635, 425)]
    pen = draw_sketch_line(draw, thread, wb_reveal(local, 3, 7), PALETTE["pink"], 6, frame, 235)
    if 0.35 < local < 0.9:
        draw_marker_hand(draw, pen[0], pen[1], -0.4, 0.64)
    for i, (text, x, y, color) in enumerate([("cierpliwość", 650, 250, "teal"), ("pomysł", 815, 255, "purple"), ("połączenia", 830, 460, "coral")]):
        wb_keyword(draw, text, x, y, wb_reveal(local, i + 4, 7), color, frame)


def wb_final(draw: ImageDraw.ImageDraw, local: float, frame: int) -> None:
    draw_wb_person(draw, 430, 250, 1.05, wb_reveal(local, 0, 6), frame, "blue")
    draw_wb_partial_text(draw, "HR", (585, 250), FONTS["giant"], PALETTE["purple"], wb_reveal(local, 1, 6))
    for i, (text, y, color) in enumerate([("otwarta", 338, "teal"), ("dobrze zorganizowana", 393, "blue"), ("gotowa na wyzwania", 448, "coral")]):
        wb_keyword(draw, text, 800, y, wb_reveal(local, i + 2, 6), color, frame)
    draw_sketch_line(draw, [(545, 395), (635, 430), (730, 395)], wb_reveal(local, 5, 6), PALETTE["mint"], 7, frame, 220)


WB_DRAWERS = {
    "intro": wb_intro,
    "twins": wb_twins,
    "restaurant": wb_restaurant,
    "gdansk": wb_gdansk,
    "award": wb_award,
    "esn": wb_esn,
    "porto": wb_porto,
    "crochet": wb_crochet,
    "final": wb_final,
}


def render_whiteboard_content(scene: Scene, t: float, frame_number: int) -> Image.Image:
    local = clamp((t - scene.start) / (scene.end - scene.start))
    img = Image.new("RGBA", (WIDTH, HEIGHT), (252, 250, 244, 255))
    draw = ImageDraw.Draw(img)
    draw_wb_background(draw, frame_number)
    draw_wb_header(draw, scene, t, local, frame_number)
    WB_DRAWERS[scene.icon](draw, local, frame_number)
    draw_wb_caption(draw, scene, local, frame_number)
    return apply_camera_motion(img, scene, local, frame_number).convert("RGB")


def whiteboard_wipe(previous: Image.Image, current: Image.Image, alpha: float) -> Image.Image:
    alpha = smootherstep(alpha)
    x = int(lerp(-WIDTH * 0.12, WIDTH * 1.12, alpha))
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    mask_draw = ImageDraw.Draw(mask)
    if x > 0:
        mask_draw.rectangle((0, 0, min(x, WIDTH), HEIGHT), fill=255)
    for edge in range(36):
        edge_x = x + edge
        if 0 <= edge_x < WIDTH:
            mask_draw.line((edge_x, 0, edge_x, HEIGHT), fill=max(0, 255 - edge * 7))
    result = Image.composite(current.convert("RGBA"), previous.convert("RGBA"), mask)
    draw = ImageDraw.Draw(result)
    draw.rounded_rectangle((x - 84, 232, x + 35, 488), radius=28, fill=(245, 245, 238, 240), outline=wb_color("ink", 160), width=3)
    draw.text((x - 58, 330), "wipe", font=FONTS["tiny"], fill=PALETTE["muted"])
    return result.convert("RGB")


def current_scene(t: float) -> Scene:
    for scene in SCENES:
        if scene.start <= t < scene.end:
            return scene
    return SCENES[-1]


def draw_background_details(draw: ImageDraw.ImageDraw, scene: Scene, frame: int) -> None:
    phase = frame / 45
    blobs = [
        (155 + math.sin(phase) * 15, 235, 115, PALETTE["yellow"]),
        (1080 + math.cos(phase * 0.8) * 25, 185, 95, PALETTE["pink"]),
        (1120, 535 + math.sin(phase * 1.2) * 20, 135, PALETTE["mint"]),
        (170, 550 + math.cos(phase * 1.1) * 18, 95, PALETTE["blue"]),
    ]
    for x, y, r, color in blobs:
        draw.ellipse((x - r, y - r, x + r, y + r), fill=color + (38,))
    for i in range(9):
        x = 130 + i * 130
        y = 610 + math.sin(phase + i) * 8
        draw.ellipse((x, y, x + 7, y + 7), fill=PALETTE["ink"] + (35,))


def render_scene_content(scene: Scene, t: float, frame_number: int) -> Image.Image:
    if WHITEBOARD_STYLE:
        return render_whiteboard_content(scene, t, frame_number)

    local = clamp((t - scene.start) / (scene.end - scene.start))
    img = BG_CACHE[(scene.bg_top, scene.bg_bottom)].copy()
    draw = ImageDraw.Draw(img)

    draw_paper_texture(draw, frame_number)
    draw_background_details(draw, scene, frame_number)
    draw_header(draw, scene, t, local)
    ICON_DRAWERS[scene.icon](draw, local, frame_number)
    draw_scene_doodles(draw, scene, local, frame_number)
    draw_caption(img, scene, local)

    return apply_camera_motion(img, scene, local, frame_number).convert("RGB")


def render_frame(frame_number: int) -> Image.Image:
    t = frame_number / FPS
    scene = current_scene(t)
    current = render_scene_content(scene, t, frame_number)

    fade_duration = 0.85
    index = scene_index(scene)
    if index > 0 and t - scene.start < fade_duration:
        previous_scene = SCENES[index - 1]
        previous = render_scene_content(previous_scene, previous_scene.end - 0.001, frame_number)
        if WHITEBOARD_STYLE:
            return whiteboard_wipe(previous, current, (t - scene.start) / fade_duration).convert("RGB")
        return slide_blend(previous, current, (t - scene.start) / fade_duration).convert("RGB")

    return current


def srt_timestamp(seconds: float) -> str:
    milliseconds = int(round((seconds - int(seconds)) * 1000))
    total_seconds = int(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"


def write_srt(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    chunks: list[str] = []
    for index, scene in enumerate(SCENES, start=1):
        text = "\n".join(textwrap.wrap(scene.caption, width=58))
        chunks.append(
            f"{index}\n"
            f"{srt_timestamp(scene.start)} --> {srt_timestamp(scene.end)}\n"
            f"{text}\n"
        )
    path.write_text("\n".join(chunks), encoding="utf-8")


def run_ffmpeg(command: list[str], input_bytes: bytes | None = None) -> None:
    try:
        subprocess.run(command, input=input_bytes, check=True)
    except FileNotFoundError as exc:
        raise SystemExit("FFmpeg is required but was not found in PATH.") from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"FFmpeg failed with exit code {exc.returncode}") from exc


def encode_video(silent_output: Path) -> None:
    silent_output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{WIDTH}x{HEIGHT}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-vf",
        "format=yuv420p",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "20",
        "-movflags",
        "+faststart",
        str(silent_output),
    ]

    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None
    total_frames = int(DURATION * FPS)
    try:
        for frame_number in range(total_frames):
            frame = render_frame(frame_number)
            process.stdin.write(frame.tobytes())
            if frame_number % FPS == 0:
                second = frame_number // FPS
                print(f"Rendering {second:02d}/{int(DURATION)}s", end="\r", flush=True)
    except BrokenPipeError as exc:
        raise SystemExit("FFmpeg stopped while receiving frames.") from exc
    finally:
        process.stdin.close()

    return_code = process.wait()
    print(" " * 40, end="\r")
    if return_code != 0:
        raise SystemExit(f"FFmpeg failed with exit code {return_code}")


def mux_voiceover(video_path: Path, voiceover_path: Path, output_path: Path) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-i",
        str(video_path),
        "-i",
        str(voiceover_path),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    run_ffmpeg(command)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Dominika Romanow's animated video CV.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Path to the MP4 output.")
    parser.add_argument("--srt", type=Path, default=DEFAULT_SRT, help="Path to the SRT subtitle output.")
    parser.add_argument("--voiceover", type=Path, help="Optional WAV/MP3/M4A voiceover to mux into the MP4.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not shutil.which("ffmpeg"):
        print("FFmpeg is required but was not found in PATH.", file=sys.stderr)
        return 1

    output: Path = args.output
    write_srt(args.srt)

    if args.voiceover:
        if not args.voiceover.exists():
            print(f"Voiceover file not found: {args.voiceover}", file=sys.stderr)
            return 1
        silent_output = output.with_name(output.stem + "_silent.mp4")
        encode_video(silent_output)
        mux_voiceover(silent_output, args.voiceover, output)
        silent_output.unlink(missing_ok=True)
    else:
        encode_video(output)

    print(f"Saved video: {output}")
    print(f"Saved subtitles: {args.srt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
