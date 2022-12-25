import argparse
from dataclasses import dataclass
import json
from random import gauss, uniform
from data import Circle, Coordinates, Line, Path, Route
from util import edit_json_file, load_map, read_json_file
from simanneal import Annealer
from constants import PRECALC_BASE_FILE
from visualizer import visualize_route
from tqdm import tqdm

import warnings

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
    # context aware
    res = [None] * segmentation
    for i in range(segmentation):
        x = l * (i + 1) / (segmentation + 1)
        y_max = min(x * cos_a / sin_a, (10000 - x * sin_a) / cos_a)
        y_min = max(-x * sin_a / cos_a, (-10000 + x * cos_a) / sin_a)
        y = uniform(y_min, y_max)
        res[i] = translate(Coordinates(x, y), cos_a, sin_a)
    return res


def straight_path_from_base(segmentation, cos_a, sin_a, l):
    # context aware
    res = [None] * segmentation
    for i in range(segmentation):
        x = l * (i + 1) / (segmentation + 1)
        y = 0
        res[i] = translate(Coordinates(x, y), cos_a, sin_a)
    return res


@dataclass
class PathFromBaseMutator:
    x_var: int
    y_var: int

    def mutate(self, path: list[Coordinates], cos_a, sin_a, l) -> list[Coordinates]:
        # context aware
        mutant = [0] * len(path)
        # knowing the constext of [base, *path, f]
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
        # context unaware
        l = Line.from_two_points(f, t)
        return sum(l.distance_in_circle(s) for s in self.circles)


@dataclass
class ObjectiveChecker:
    penalty: callable

    def objective(self, path: list[Coordinates]):
        # TODO: optimize:
        # write is_len_smaller(path, len) instead
        # that returns the actual len of the path only in case when it is smaller,
        # so it can throw summation of path pieces if it finds that the sum is already bigger that the threshold

        # context unaware
        res = 0
        prev = path[0]
        for pos in path[1:]:
            res += prev.dist(pos) + 6 * self.penalty(pos, prev)
            prev = pos
        return res


class OprimalPathFromBaseFinder:
    segmentation: int
    mutate: callable  # context aware
    objective: callable  # context unaware
    rand_path_from_base: callable  # context aware
    schedule: dict = {"tmax": 100.0, "tmin": 1, "steps": 340, "updates": 100}

    def __init__(
        self,
        segmentation,
        mutate,
        objective,
        rand_path_from_base_generator=None,
        schedule=None,
    ):
        self.segmentation = segmentation
        self.mutate = mutate
        self.objective = objective
        if rand_path_from_base_generator is None:
            self.rand_path_from_base = rand_path_from_base
        else:
            self.rand_path_from_base = rand_path_from_base_generator
        if schedule is not None:
            self.schedule = schedule

    def optimal_path(self, f: Coordinates) -> Path:
        mutate = self.mutate
        objective = self.objective

        l = f.dist(base)
        if l < 200:
            return Path([base, f], objective([base, f]))

        cos_a = f.x / l
        sin_a = f.y / l

        class PathAnnealer(Annealer):
            def move(self):
                path = [base] + mutate(self.state.path[1:-1], cos_a, sin_a, l) + [f]
                length = objective(path)
                self.state = Path(path, length)

            def energy(self):
                return self.state.length

        init = (
            [base] + self.rand_path_from_base(self.segmentation, cos_a, sin_a, l) + [f]
        )
        annealer = PathAnnealer(Path(init, objective(init)))
        annealer.set_schedule(self.schedule)
        best, cost = annealer.anneal()
        linear = Path([base, f], objective([base, f]))
        if cost > linear.length:
            return linear
        # NOTE: assuming int rounding does not change path len significantly
        return Path([Coordinates(int(c.x), int(c.y)) for c in best.path], cost)


# TODO: bunch calculations
def main():
    warnings.filterwarnings("ignore")
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--point", type=Coordinates.from_str)
    parser.add_argument("-i", "--index", type=int)
    parser.add_argument("-b", "--bunch", action="store_true")
    parser.add_argument("-v", "--visualize", action="store_true")
    args = parser.parse_args()

    sus_map = load_map()

    circles = [Circle.from_snow(s) for s in sus_map.snow_areas]
    penalty = PenatyChecker(circles).penalty
    objective = ObjectiveChecker(penalty).objective

    def optimal_path(f: Coordinates) -> Path:
        segmentation = int(f.dist(base) // 2000)
        return OprimalPathFromBaseFinder(
            segmentation,
            PathFromBaseMutator(4000, 4000).mutate,
            objective,
            schedule={"tmax": 100, "tmin": 1, "steps": 500, "updates": 500},
        ).optimal_path(f)

    if args.bunch:
        print("enter points: ")
        points = json.loads(input())
        with edit_json_file(PRECALC_BASE_FILE) as precalc:
            for p in tqdm(points):
                precalc[p] = optimal_path(Coordinates.from_str(p)).to_dict()
        return

    if args.point is None:
        args.point = sus_map.children[args.index]

    k = args.point.to_str()
    if args.visualize:
        with read_json_file(PRECALC_BASE_FILE) as res:
            if k not in res:
                print("No such point")
            else:
                path = Path.from_dict(res[k])
                print(
                    "objective:",
                    path.length,
                )
                print("path:", path.path[1:-1])
                print("draw? (y/n): ")
                if input() == "y":
                    visualize_route(sus_map, Route(path.path, None, None)).save(
                        "data/path.png"
                    )
    else:
        print("linear: ", base.dist(args.point) + 6 * penalty(base, args.point))
        with read_json_file(PRECALC_BASE_FILE) as res:
            if k not in res:
                print("no previous results")
            else:
                print("best: ", Path.from_dict(res[k]).length)

        best_path = optimal_path(args.point)

        with edit_json_file(PRECALC_BASE_FILE) as res:
            if k not in res:
                res[k] = Path([], 1e100).to_dict()
            old = Path.from_dict(res[k])
            if old.length > best_path.length:
                res[k] = best_path.to_dict()
                print("update")

        print("draw? (y/n): ")
        if input() == "y":
            visualize_route(sus_map, Route(best_path.path, None, None)).save(
                "data/path.png"
            )


if __name__ == "__main__":
    main()
