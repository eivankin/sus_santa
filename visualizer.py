from PIL import Image, ImageDraw
from data import Coordinates, Map, Route
from util import load_map, info_about_map

IMAGE_SIZE = 10000, 10000
HOUSE_SIZE = 15

BACKGROUND_COLOR = (0, 0, 0)
SNOW_AREA_COLOR = (0, 0, 255)
HOUSE_COLOR = (0, 255, 0)
START_COLOR = (255, 255, 255)
ROUTE_COLOR = (255, 255, 255)


def visualize_map(m: Map) -> Image:
    info_about_map(m)

    print(" === DRAWING === ")

    image = Image.new("RGB", IMAGE_SIZE, BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    draw.rectangle(((0, 0), (10, 10)), START_COLOR)

    for area in m.snow_areas:
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
                child.y + HOUSE_SIZE,
            ),
            fill=HOUSE_COLOR,
        )

    return image


def visualize_route(m: Map, r: Route) -> Image:
    image = visualize_map(m)
    draw = ImageDraw.Draw(image)

    draw.line([(c.x, c.y) for c in r.moves], fill=ROUTE_COLOR, width=5, joint="curve")

    return image


if __name__ == "__main__":
    with open("data/map.json") as f:
        visualize_map(load_map()).save("data/map.png")
