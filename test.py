import os
from random import gauss, uniform
from annealer import simulated_annealing
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

    def optimal_path_from_base_to(f: Coordinates) -> list[Coordinates]:
        segmentation = 5

        l = f.dist(base)
        cos_a = f.x / l
        sin_a = f.y / l

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
            return res * 0.001

        def mutate(path):
            nonlocal f
            mutant = [0] * len(path)
            for i, pos in enumerate(path):
                p = retranslate(pos)
                y_max = min(p.x * cos_a / sin_a, (10000 - p.x * sin_a) / cos_a)
                y_min = max(-p.x * sin_a / cos_a, (-10000 + p.x * cos_a) / sin_a)
                p.y = gauss(p.y, 300)
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
        annealer.set_schedule(annealer.auto(minutes=0.1))
        return [Coordinates(int(c.x), int(c.y)) for c in annealer.anneal()[0]]

    end = Coordinates(3000, 9000)
    base = Coordinates(0, 0)
    path = [base]
    path.extend(optimal_path_from_base_to(end))
    path.append(end)

    r = Route(path, None, None)
    visualize_route(sus_map, r).save("data/route.png")
