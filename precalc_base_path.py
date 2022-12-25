import argparse
from dataclasses import dataclass
from random import gauss, uniform
from data import Circle, Coordinates, Line, Map, Route
from util import edit_json_file, load_map, read_json_file
from simanneal import Annealer
from constants import PRECALC_BASE_FILE
from visualizer import visualize_route

# ['"741 104"', '"55 563"', '"1850 954"', '"539 715"', '"1100 3542"', '"1501 1125"', '"5955 977"', '"233 2245"', '"1043 3184"', '"2405 67"', '"5141 2860"', '"2212 1602"', '"3007 3303"', '"318 1833"', '"3970 2086"', '"3450 2538"', '"3340 3614"', '"3297 3473"', '"6264 2788"', '"2834 3160"', '"5579 1388"', '"2602 950"', '"6777 12"', '"83 5255"', '"1298 3041"', '"5012 3734"', '"5549 5831"', '"5568 27"', '"9161 1142"', '"4052 4091"', '"2429 5144"', '"5487 3357"', '"6828 5434"', '"610 6431"', '"2056 8546"', '"7028 1212"', '"7738 1853"', '"4837 5355"', '"4887 7627"', '"6141 3955"', '"8211 3997"', '"2153 3174"', '"3398 5881"', '"106 7720"', '"1308 9380"', '"4189 4335"', '"6403 7937"', '"240 8729"', '"1721 9369"', '"7772 5596"', '"8997 6205"', '"7460 2195"', '"4474 4298"', '"5144 8480"', '"8346 5382"', '"9317 6048"', '"8947 6171"', '"9533 4756"', '"4691 2104"', '"6518 9112"', '"8691 6567"', '"9738 4684"', '"1422 2827"', '"1186 6669"', '"9193 410"', '"8728 4939"', '"1000 9866"', '"9102 6683"', '"7098 9835"', '"7549 8173"', '"5857 9106"', '"1224 6860"', '"3248 6228"', '"7352 8248"', '"4619 9864"', '"6941 2173"', '"8891 9224"', '"9600 77"', '"8965 9653"', '"9060 9891"', '"8516 8498"', '"1003 4361"', '"3490 7751"', '"8381 8634"', '"3241 7138"', '"1403 4153"', '"3593 9895"', '"3536 6893"', '"6312 9952"']

base = Coordinates(0, 0)


def translate(pos: Coordinates, cos_a, sin_a) -> Coordinates:
    # represent back from the rotated coordinate system
    return Coordinates(
        pos.x * cos_a - pos.y * sin_a,
        pos.x * sin_a + pos.y * cos_a,
    )


def retranslate(pos: Coordinates, cos_a, sin_a) -> Coordinates:
    # represent in the rotated coordinate system
    return Coordinates(
        pos.x * cos_a + pos.y * sin_a,
        pos.y * cos_a - pos.x * sin_a,
    )


def rand_path_from_base(segmentation, cos_a, sin_a, l):
    res = [None] * segmentation
    for i in range(segmentation):
        x = l * (i + 1) / (segmentation + 1)
        y_max = min(x * cos_a / sin_a, (10000 - x * sin_a) / cos_a)
        y_min = max(-x * sin_a / cos_a, (-10000 + x * cos_a) / sin_a)
        y = uniform(y_min, y_max)
        res[i] = translate(Coordinates(x, y), cos_a, sin_a)
    return res


@dataclass
class PathFromBaseMutator:
    x_var: int
    y_var: int

    def mutate(self, path, cos_a, sin_a, l):
        mutant = [0] * len(path)
        rpath = [Coordinates(10, 0)]
        rpath.extend(retranslate(pos, cos_a, sin_a) for pos in path)
        rpath.append(Coordinates(l - 10, 0))
        for i, p in enumerate(rpath[1:-1]):
            x_max = rpath[i + 2].x - 1
            x_min = rpath[i].x + 1
            if x_max > x_min:
                p.x = gauss(p.x, self.x_var)
                p.x = max(x_min, min(x_max, p.x))
            y_max = min(p.x * cos_a / sin_a, (10000 - p.x * sin_a) / cos_a)
            y_min = max(-p.x * sin_a / cos_a, (-10000 + p.x * cos_a) / sin_a)
            p.y = gauss(p.y, self.y_var)
            p.y = max(y_min, min(y_max, p.y))
            mutant[i] = translate(p, cos_a, sin_a)
        return mutant


@dataclass
class PenatyChecker:
    circles: list[Circle]

    def penalty(self, f: Coordinates, t: Coordinates) -> float:
        l = Line.from_two_points(f, t)
        return sum(l.distance_in_circle(s) for s in self.circles)


@dataclass
class ObjectiveChecker:
    penalty: callable

    def objective(self, start, path, stop):
        res = 0
        prev = start
        for pos in path:
            res += prev.dist(pos) + 6 * self.penalty(pos, prev)
            prev = pos
        res += prev.dist(stop) + 6 * self.penalty(stop, prev)
        return res


class OprimalPathFromBaseFinder:
    segmentation: int
    objective_checker: ObjectiveChecker
    mutate: callable
    rand_path_from_base: callable
    schedule: dict = {"tmax": 100.0, "tmin": 1, "steps": 340, "updates": 100}

    def __init__(
        self,
        segmentation,
        objectivec,
        mutate,
        rand_path_from_base_generator=None,
        schedule=None,
    ):
        self.segmentation = segmentation
        self.objective_checker = objectivec
        self.mutate = mutate
        if rand_path_from_base_generator is None:
            self.rand_path_from_base = rand_path_from_base
        else:
            self.rand_path_from_base = rand_path_from_base_generator
        if schedule is not None:
            self.schedule = schedule

    def optimal_path(self, f: Coordinates) -> list[Coordinates]:
        l = f.dist(base)
        cos_a = f.x / l
        sin_a = f.y / l

        mutate = self.mutate
        objective = self.objective_checker.objective
        penalty = self.objective_checker.penalty

        class PathAnnealer(Annealer):
            def move(self):
                self.state = mutate(self.state, cos_a, sin_a, l)

            def energy(self):
                nonlocal f
                return objective(base, self.state, f)

        annealer = PathAnnealer(
            self.rand_path_from_base(self.segmentation, cos_a, sin_a, l)
        )
        annealer.set_schedule(self.schedule)
        best, cost = annealer.anneal()
        if cost > l + 6 * penalty(base, f):
            return []
        return [Coordinates(int(c.x), int(c.y)) for c in best]


def point_data(s: str) -> Coordinates:
    return Coordinates(*map(float, s.split(" ")))


def main():
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
    penalty = PenatyChecker(circles).penalty
    objective_ch = ObjectiveChecker(penalty)
    objective = objective_ch.objective

    if args.visualize:
        with read_json_file(PRECALC_BASE_FILE) as res:
            if str(args.index) not in res:
                print("No such index")
            else:
                path = [Coordinates.from_dict(e) for e in res[str(args.index)]]
                print(
                    "objective:",
                    objective(base, path, point),
                )
                print("path:", path)
                print("draw? (y/n): ")
                if input() == "y":
                    spath = path
                    path = [base]
                    path.extend(spath)
                    path.append(point)
                    visualize_route(sus_map, Route(path, None, None)).save(
                        "data/path.png"
                    )
    else:
        segmentation = 2
        print("linear: ", base.dist(point) + 6 * penalty(base, point))
        with read_json_file(PRECALC_BASE_FILE) as res:
            if str(args.index) not in res:
                print("no previous results")
            else:
                path = [Coordinates.from_dict(e) for e in res[str(args.index)]]
                print("best: ", objective(base, path, point))
        optimal_path_from_base_to = OprimalPathFromBaseFinder(
            segmentation,
            objective_ch,
            PathFromBaseMutator(4000, 4000).mutate,
            schedule={"tmax": 1000, "tmin": 1, "steps": 3e3, "updates": 1e3},
        ).optimal_path
        best_path = optimal_path_from_base_to(point)

        with edit_json_file(PRECALC_BASE_FILE) as res:
            if str(args.index) not in res:
                res[str(args.index)] = []
            old = [Coordinates.from_dict(e) for e in res[str(args.index)]]
            if objective(base, old, point) > objective(base, best_path, point):
                res[str(args.index)] = [e.to_dict() for e in best_path]
                print("update")

        print("draw? (y/n): ")
        if input() == "y":
            path = [base]
            path.extend(best_path)
            path.append(point)
            visualize_route(sus_map, Route(path, None, None)).save("data/path.png")


if __name__ == "__main__":
    main()
