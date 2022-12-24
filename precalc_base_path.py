import argparse
from random import gauss, uniform
from data import Circle, Coordinates, Line, Map, Route
from util import edit_json_file, load_map
from simanneal import Annealer
from constants import PRECALC_BASE_FILE
from visualizer import visualize_route

# TODO: in use by playground

base = Coordinates(0, 0)


def penalty(f: Coordinates, t: Coordinates) -> float:
    l = Line.from_two_points(f, t)
    return sum(l.distance_in_circle(s) for s in circles)


def objective(path, f):
    global base
    res = 0
    prev = f
    for pos in path:
        res += prev.dist(pos) + 6 * penalty(pos, prev)
        prev = pos
    res += prev.dist(base) + 6 * penalty(base, prev)
    return res


def point_data(s: str) -> Coordinates:
    return Coordinates(*map(float, s.split(" ")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("index", type=int)
    parser.add_argument("-p", "--point", type=point_data)
    parser.add_argument("-v", "--visualize", action="store_true")
    args = parser.parse_args()

    sus_map = load_map()

    if args.point is not None:
        point = args.point
        for i, child in enumerate(sus_map.children):
            if child.x == point.x and child.y == point.y:
                args.index = i
                break
    else:
        point = sus_map.children[args.index]

    circles = [Circle.from_snow(s) for s in sus_map.snow_areas]

    if args.visualize:
        with edit_json_file(PRECALC_BASE_FILE) as res:
            if str(args.index) not in res:
                print("No such index")
            else:
                path = [Coordinates.from_dict(e) for e in res[str(args.index)]]
                print(
                    "objective:",
                    objective(path, point),
                )
                print("path:", path)
                spath = path
                path = [base]
                path.extend(spath)
                path.append(point)
        visualize_route(sus_map, Route(path, None, None)).save("data/path.png")
    else:

        def optimal_path_from_base_to(f: Coordinates) -> list[Coordinates]:
            segmentation = 2

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

            def mutate(path):
                nonlocal f
                mutant = [0] * len(path)
                rpath = [Coordinates(0, 0)]
                rpath.extend(retranslate(pos) for pos in path)
                rpath.append(Coordinates(l, 0))
                for i, p in enumerate(rpath[1:-1]):
                    x_max = rpath[i + 2].x
                    x_min = rpath[i].x
                    p.x = gauss(p.x, 4000)
                    p.x = max(x_min, min(x_max, p.x))
                    y_max = min(p.x * cos_a / sin_a, (10000 - p.x * sin_a) / cos_a)
                    y_min = max(-p.x * sin_a / cos_a, (-10000 + p.x * cos_a) / sin_a)
                    p.y = gauss(p.y, 4000)
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
                    nonlocal f
                    return objective(self.state, f)

            annealer = PathAnnealer(rand_path())
            annealer.set_schedule(
                {"tmax": 100.0, "tmin": 1, "steps": 3e3, "updates": 1e3}
            )
            print(f.dist(base) + 6 * penalty(base, f))
            best, cost = annealer.anneal()
            if cost > f.dist(base) + 6 * penalty(base, f):
                return []
            return [Coordinates(int(c.x), int(c.y)) for c in best]

        best_path = optimal_path_from_base_to(point)
        with edit_json_file(PRECALC_BASE_FILE) as res:
            if str(args.index) not in res:
                res[str(args.index)] = []
            old = [Coordinates.from_dict(e) for e in res[str(args.index)]]
            if objective(old, point) > objective(best_path, point):
                res[str(args.index)] = [e.to_dict() for e in best_path]
