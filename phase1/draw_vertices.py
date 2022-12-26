from PIL import ImageDraw

from data import Circle
from util import load_map
from visualizer import visualize_map, HOUSE_SIZE

if __name__ == '__main__':
    map_data = load_map()
    octagon_vertices = sum((Circle.from_snow(s).get_outer_points()
                            for s in map_data.snow_areas), [])
    img = visualize_map(map_data)
    draw = ImageDraw.Draw(img)
    for v in octagon_vertices:
        draw.rectangle(
            (
                v.x - HOUSE_SIZE,
                v.y - HOUSE_SIZE,
                v.x + HOUSE_SIZE,
                v.y + HOUSE_SIZE,
            ),
            fill=(255, 0, 0),
        )
    img.save("./data/octo.png")
