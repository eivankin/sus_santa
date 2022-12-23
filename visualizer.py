from PIL import Image, ImageDraw

from util import load_map, info_about_map

IMAGE_SIZE = 10000, 10000
HOUSE_SIZE = 15

BACKGROUND_COLOR = (0, 0, 0)
SNOW_AREA_COLOR = (0, 0, 255)
HOUSE_COLOR = (0, 255, 0)
START_COLOR = (255, 255, 255)

with open("data/map.json") as f:
    m = load_map()
    info_about_map(m)

    print(" === DRAWING === ")

    image = Image.new("RGB", IMAGE_SIZE, BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    draw.rectangle(((0, 0), (10, 10)), START_COLOR)

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
