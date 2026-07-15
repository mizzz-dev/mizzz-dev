from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

W, H = 1600, 640
BG_TOP = (6, 8, 20)
BG_BOTTOM = (22, 13, 42)
PURPLE = (150, 92, 255)
VIOLET = (106, 82, 255)
CYAN = (74, 226, 255)
PINK = (255, 85, 181)
WHITE = (241, 239, 255)
MUTED = (171, 169, 198)
GRID = (91, 75, 130)

random.seed(42)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def gradient(width: int, height: int) -> Image.Image:
    image = Image.new("RGB", (width, height))
    pixels = image.load()
    for y in range(height):
        vertical = y / max(1, height - 1)
        for x in range(width):
            diagonal = x / max(1, width - 1)
            glow = max(0.0, 1.0 - math.dist((diagonal, vertical), (0.72, 0.28)) / 0.75)
            red = int(BG_TOP[0] * (1 - vertical) + BG_BOTTOM[0] * vertical + 17 * glow)
            green = int(BG_TOP[1] * (1 - vertical) + BG_BOTTOM[1] * vertical + 7 * glow)
            blue = int(BG_TOP[2] * (1 - vertical) + BG_BOTTOM[2] * vertical + 28 * glow)
            pixels[x, y] = (min(255, red), min(255, green), min(255, blue))
    return image


def add_stars(image: Image.Image, count: int = 170) -> None:
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for _ in range(count):
        x = random.randrange(0, image.width)
        y = random.randrange(0, int(image.height * 0.64))
        radius = random.choice([1, 1, 1, 2])
        alpha = random.randrange(70, 210)
        color = random.choice([WHITE, CYAN, PURPLE])
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, alpha))
    image.alpha_composite(layer)


def glow_line(layer: Image.Image, points, color, width: int = 3, blur: int = 10) -> None:
    glow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.line(points, fill=(*color, 150), width=width * 4, joint="curve")
    glow = glow.filter(ImageFilter.GaussianBlur(blur))
    layer.alpha_composite(glow)
    ImageDraw.Draw(layer).line(points, fill=(*color, 235), width=width, joint="curve")


def draw_moon(layer: Image.Image) -> None:
    draw = ImageDraw.Draw(layer)
    center_x, center_y, radius = 1180, 136, 104
    glow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse(
        (center_x - radius - 25, center_y - radius - 25, center_x + radius + 25, center_y + radius + 25),
        fill=(*PURPLE, 80),
    )
    layer.alpha_composite(glow.filter(ImageFilter.GaussianBlur(30)))
    draw.ellipse(
        (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
        fill=(205, 192, 238, 235),
        outline=(255, 255, 255, 165),
        width=2,
    )
    draw.ellipse(
        (center_x - radius + 52, center_y - radius - 8, center_x + radius + 60, center_y + radius + 18),
        fill=(19, 15, 40, 245),
    )


def draw_skyline(layer: Image.Image) -> None:
    draw = ImageDraw.Draw(layer)
    base = 420
    points = [(0, base)]
    x = 0
    while x < W:
        peak = random.randrange(290, 405)
        points.extend([(x, base), (x + random.randrange(25, 70), peak)])
        x += random.randrange(65, 125)
    points.extend([(W, base), (W, H), (0, H)])
    draw.polygon(points, fill=(9, 11, 26, 235))

    for x in range(40, W, 82):
        building_height = random.randrange(35, 105)
        building_width = random.randrange(18, 36)
        draw.rectangle((x, base - building_height, x + building_width, base), fill=(10, 13, 31, 255))
        if random.random() > 0.45:
            draw.polygon(
                [
                    (x + building_width // 2, base - building_height - random.randrange(18, 45)),
                    (x, base - building_height),
                    (x + building_width, base - building_height),
                ],
                fill=(10, 13, 31, 255),
            )
        for window_y in range(base - building_height + 15, base - 8, 18):
            if random.random() > 0.38:
                draw.rectangle((x + 6, window_y, x + 9, window_y + 6), fill=(*PURPLE, 120))


def draw_road(layer: Image.Image, offset: int = 0) -> None:
    draw = ImageDraw.Draw(layer)
    horizon = 394
    draw.polygon([(580, H), (1020, H), (865, horizon), (730, horizon)], fill=(8, 10, 23, 255))
    glow_line(layer, [(580, H), (730, horizon)], CYAN, 2, 12)
    glow_line(layer, [(1020, H), (865, horizon)], PINK, 2, 12)
    for index in range(9):
        progress = ((index * 0.14 + offset / 100) % 1.0)
        y = int(horizon + (H - horizon) * (progress**1.8))
        half_width = int(6 + 26 * progress)
        draw.line(
            (800 - half_width, y, 800 + half_width, y),
            fill=(235, 235, 255, 155),
            width=max(1, int(1 + 4 * progress)),
        )


def draw_car(layer: Image.Image) -> None:
    draw = ImageDraw.Draw(layer)
    glow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((920, 432, 1500, 610), fill=(*PURPLE, 95))
    layer.alpha_composite(glow.filter(ImageFilter.GaussianBlur(28)))

    body = [
        (960, 520), (1010, 470), (1120, 448), (1288, 452), (1390, 494),
        (1475, 510), (1505, 552), (1450, 575), (1010, 575), (950, 555),
    ]
    draw.polygon(body, fill=(13, 16, 31, 255), outline=(148, 119, 219, 230))
    draw.polygon(
        [(1082, 474), (1148, 454), (1270, 458), (1345, 492), (1115, 492)],
        fill=(36, 42, 70, 245),
        outline=(91, 214, 255, 180),
    )
    draw.line([(1020, 517), (1425, 517)], fill=(*PURPLE, 215), width=3)
    for center_x in (1080, 1390):
        draw.ellipse((center_x - 51, 526, center_x + 51, 628), fill=(5, 6, 12, 255), outline=(88, 81, 117, 255), width=5)
        draw.ellipse((center_x - 27, 550, center_x + 27, 604), fill=(31, 30, 47, 255), outline=(169, 150, 215, 220), width=3)
        draw.ellipse((center_x - 7, 570, center_x + 7, 584), fill=(*CYAN, 180))
    glow_line(layer, [(970, 527), (1030, 507)], CYAN, 3, 13)
    glow_line(layer, [(1440, 515), (1490, 526)], PINK, 3, 13)


def rounded_panel(draw: ImageDraw.ImageDraw, box, radius: int = 22, fill=(13, 16, 33, 210), outline=(147, 112, 222, 110), width: int = 2) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_hud(layer: Image.Image) -> None:
    draw = ImageDraw.Draw(layer)
    draw.text((96, 100), "mizzz", font=font(104, True), fill=WHITE)
    draw.text((102, 220), "BUILD / DRIVE / CREATE", font=font(26, True), fill=CYAN)
    draw.text((102, 266), "Frontend-focused Full Stack Developer", font=font(22), fill=MUTED)
    draw.text((102, 300), "Anime  •  Cars  •  Gadgets  •  Product Engineering", font=font(18), fill=(177, 151, 220))
    glow_line(layer, [(96, 338), (492, 338)], PURPLE, 2, 10)

    cards = [
        ((105, 388, 310, 478), "ivRoom", "COMMUNITY"),
        ((325, 388, 530, 478), "Lunaria", "BOT / OPS"),
        ((105, 492, 310, 582), "Quizverse", "LEARNING"),
        ((325, 492, 530, 582), "RouteGarage", "MOBILITY"),
    ]
    for box, title, label in cards:
        rounded_panel(draw, box)
        draw.text((box[0] + 18, box[1] + 16), title, font=font(21, True), fill=WHITE)
        draw.text((box[0] + 18, box[1] + 52), label, font=font(12, True), fill=PURPLE)
        draw.ellipse((box[2] - 32, box[1] + 18, box[2] - 18, box[1] + 32), fill=(*CYAN, 210))

    center_x, center_y = 1445, 132
    for radius, color, start in [(72, PURPLE, 205), (52, CYAN, 230), (32, PINK, 250)]:
        draw.arc((center_x - radius, center_y - radius, center_x + radius, center_y + radius), start=start, end=520, fill=(*color, 220), width=4)
    draw.text((1408, 118), "96", font=font(30, True), fill=WHITE)
    draw.text((1396, 154), "IDEAS", font=font(10, True), fill=MUTED)

    rounded_panel(draw, (1292, 245, 1536, 386), radius=18, fill=(11, 14, 31, 205), outline=(67, 210, 255, 90))
    draw.text((1315, 265), "DEVICE LINK", font=font(14, True), fill=CYAN)
    labels = [("KEYBOARD", 0.84), ("AUDIO", 0.72), ("DISPLAY", 0.91)]
    for index, (name, value) in enumerate(labels):
        y = 307 + index * 25
        draw.text((1315, y), name, font=font(10, True), fill=MUTED)
        draw.rounded_rectangle((1389, y + 2, 1510, y + 10), radius=4, fill=(38, 40, 62, 220))
        draw.rounded_rectangle((1389, y + 2, 1389 + int(121 * value), y + 10), radius=4, fill=(*PURPLE, 220))


def make_hero() -> None:
    base = gradient(W, H).convert("RGBA")
    add_stars(base)
    scene = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw_moon(scene)
    draw_skyline(scene)
    draw_road(scene)
    draw_car(scene)
    draw_hud(scene)
    base.alpha_composite(scene)
    base.convert("RGB").save(ASSETS / "profile-hero.png", optimize=True, quality=94)


def make_motion() -> None:
    frame_width, frame_height = 1200, 180
    frames = []
    for frame_index in range(28):
        progress = frame_index / 28.0
        image = Image.new("RGBA", (frame_width, frame_height), (7, 9, 20, 255))
        draw = ImageDraw.Draw(image)

        for x in range(-100, frame_width + 100, 44):
            shifted_x = x + int((progress * 44) % 44)
            draw.line((shifted_x, 0, shifted_x, frame_height), fill=(*GRID, 32), width=1)
        for y in range(14, frame_height, 28):
            draw.line((0, y, frame_width, y), fill=(*GRID, 24), width=1)

        streak = Image.new("RGBA", (frame_width, frame_height), (0, 0, 0, 0))
        streak_draw = ImageDraw.Draw(streak)
        for index, color in enumerate((CYAN, PURPLE, PINK)):
            x = int(((progress + index * 0.31) % 1.25) * (frame_width + 420)) - 210
            y = 118 + index * 13
            streak_draw.line((x - 190, y, x + 110, y), fill=(*color, 205), width=3)
        image.alpha_composite(streak.filter(ImageFilter.GaussianBlur(7)))

        center_x, center_y = 1010, 90
        draw.ellipse((center_x - 57, center_y - 57, center_x + 57, center_y + 57), outline=(*PURPLE, 75), width=2)
        start = int(progress * 360)
        draw.arc((center_x - 48, center_y - 48, center_x + 48, center_y + 48), start=start, end=start + 225, fill=(*CYAN, 230), width=4)
        draw.arc((center_x - 36, center_y - 36, center_x + 36, center_y + 36), start=-start, end=-start + 165, fill=(*PINK, 205), width=3)

        draw.text((58, 45), "LIVE BUILD SIGNAL", font=font(18, True), fill=CYAN)
        draw.text((58, 79), "anime-inspired visuals  /  car culture  /  gadgets  /  code", font=font(22), fill=WHITE)
        draw.text((58, 119), "SHIP SMALL  •  POLISH FAST  •  OPERATE SAFELY", font=font(14, True), fill=(171, 151, 216))
        for index in range(6):
            alpha = int(90 + 165 * max(0, math.sin((progress * math.tau) + (index * 0.65))))
            draw.ellipse((850 + index * 20, 146, 858 + index * 20, 154), fill=(*PURPLE, alpha))

        frames.append(image.convert("P", palette=Image.Palette.ADAPTIVE, colors=96))

    frames[0].save(
        ASSETS / "profile-motion.gif",
        save_all=True,
        append_images=frames[1:],
        duration=70,
        loop=0,
        optimize=True,
        disposal=2,
    )


def clean_old_lunaris_assets() -> None:
    for path in ASSETS.glob("lunaris-*.svg"):
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    clean_old_lunaris_assets()
    make_hero()
    make_motion()
    print("Generated profile-hero.png and profile-motion.gif")
