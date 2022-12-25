import os
from random import gauss, uniform
from constants import MAP_FILE_PATH
from data import Circle, Coordinates, Line, Route
from util import get_map, load_map, save_map
from visualizer import visualize_route
from simanneal import Annealer


if __name__ == "__main__":
    if not os.path.exists(MAP_FILE_PATH):
        sus_map = get_map()
        save_map(sus_map)
    else:
        sus_map = load_map()

    circles = [Circle.from_snow(s) for s in sus_map.snow_areas]

    def penalty(f: Coordinates, t: Coordinates) -> float:
        l = Line.from_two_points(f, t)
        return sum(l.distance_in_circle(s) for s in circles)

    def optimal_path(f: Coordinates, t: Coordinates) -> list[Coordinates]:
        segmentation = int(f.dist(t) // 2000)
        print(segmentation)
        if segmentation == 0:
            return []

        l = f.dist(t)
        cos_a = (t.x - f.x) / l
        sin_a = (t.y - f.y) / l

        def translate(pos: Coordinates) -> Coordinates:
            return Coordinates(
                pos.x * cos_a - pos.y * sin_a,
                pos.x * sin_a + pos.y * cos_a,
            )

        def retranslate(pos: Coordinates) -> Coordinates:
            return Coordinates(
                pos.x * cos_a + pos.y * sin_a,
                pos.y * cos_a - pos.x * sin_a,
            )

        def objective(path):
            nonlocal f
            res = 0
            prev = f
            for pos in path:
                res += prev.dist(pos) + 6 * penalty(pos, prev)
                prev = pos
            res += prev.dist(base) + 6 * penalty(base, prev)
            return res

        def mutate(path):
            nonlocal f
            mutant = [0] * len(path)
            rpath = [Coordinates(0, 0)]
            rpath.extend(retranslate(pos) for pos in path)
            rpath.append(Coordinates(l, 0))
            for i, p in enumerate(rpath[1:-1]):
                x_max = rpath[i + 2].x
                x_min = rpath[i].x
                p.x = gauss(p.x, 2000)
                p.x = max(x_min, min(x_max, p.x))
                y_max = min(p.x * cos_a / sin_a, (10000 - p.x * sin_a) / cos_a)
                y_min = max(-p.x * sin_a / cos_a, (-10000 + p.x * cos_a) / sin_a)
                p.y = gauss(p.y, 2000)
                p.y = max(y_min, min(y_max, p.y))
                mutant[i] = translate(p)
            return mutant

        def rand_path():
            nonlocal f
            res = [None] * segmentation
            for i in range(segmentation):
                x = l * (i + 1) / (segmentation + 1)
                y_max = min(x * cos_a / sin_a, (10000 - x * sin_a) / cos_a)
                y_min = max(-x * sin_a / cos_a, (-10000 + x * cos_a) / sin_a)
                y = uniform(y_min, y_max)
                res[i] = translate(Coordinates(x, y))
            return res

        class PathAnnealer(Annealer):
            def move(self):
                self.state = mutate(self.state)

            def energy(self):
                return objective(self.state)

        annealer = PathAnnealer(rand_path())
        annealer.set_schedule({"tmax": 100.0, "tmin": 1, "steps": 320, "updates": 100})
        print(f.dist(base) + 6 * penalty(base, f))
        best, cost = annealer.anneal()
        print(cost)
        if cost > f.dist(base) + 6 * penalty(base, f):
            return []
        return [Coordinates(int(c.x), int(c.y)) for c in best]

    end = Coordinates(8000, 9600)
    start = Coordinates(0, 0)
    path = [start]
    path.extend(optimal_path(start, end))
    path.append(end)

    r = Route(path, None, None)
    visualize_route(sus_map, r).save("data/path.png")
