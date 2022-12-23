from PIL import Image, ImageDraw

from util import load_map

IMAGE_SIZE = 10000, 10000
HOUSE_SIZE = 5

BACKGROUND_COLOR = (0, 0, 0)
SNOW_AREA_COLOR = (0, 0, 255)
HOUSE_COLOR = (0, 255, 0)

with open("data/map.json") as f:
    m = load_map()

    min_x, min_y, max_x, max_y = 1e10, 1e10, 0, 0
    for child in m.children:
        min_x = min(min_x, child.x)
        min_y = min(min_y, child.y)
        max_x = max(max_x, child.x)
        max_y = max(max_y, child.y)
    print(f"{min_x=}, {min_y=}, {max_x=}, {max_y=}")

    image = Image.new("RGB", IMAGE_SIZE, BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    for area in m.snowAreas:
        draw.ellipse(
            (
                area.x - area.r,
                area.y - area.r,
                area.x + area.r,
                area.y + area.r,
            ),
            fill=SNOW_AREA_COLOR,
        )

    for child in m.children:
        draw.rectangle(
            (
                child.x - HOUSE_SIZE,
                child.y - HOUSE_SIZE,
                child.x + HOUSE_SIZE,
                child.y + HOUSE_SIZE
            ),
            fill=HOUSE_COLOR
        )

    image.save("data/map.png")
