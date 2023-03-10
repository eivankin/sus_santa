from dataclasses import dataclass
from random import gauss, uniform
import warnings
from data import Circle, Coordinates, Line, Path, Route
from simanneal import Annealer
from util import segment_time

from util import load_map

from visualizer import visualize_route


@dataclass
class SnowDistEstimator:
    circles: list[Circle]

    def snow_dist(self, f: Coordinates, t: Coordinates) -> float:
        # context unaware
        l = Line.from_two_points(f, t)
        return sum(l.distance_in_circle(s) for s in self.circles)


@dataclass
class ObjectiveChecker:
    snow_dist_estimator: callable

    def objective(self, path: list[Coordinates]):
        # context unaware
        res = 0
        prev = path[0]
        for pos in path[1:]:
            res += segment_time(
                prev.dist(pos),
                self.snow_dist_estimator(pos, prev),
                direction=pos - prev,
            )
            prev = pos
        return res


# NOTE: after application of such a objective checker, the generated path may contain repeated points!
# because this function does not throw on same points, but just puts an big cost for them,
# so if the annealer didn't do a lot of steps, it can stop with a solution with repeated points
@dataclass
class CondescendingObjectiveChecker:
    snow_dist_estimator: callable

    def objective(self, path: list[Coordinates]):
        # context unaware
        res = 0
        prev = path[0]
        for pos in path[1:]:
            dist = prev.dist(pos)
            if dist == 0:
                return 1e100
            else:
                res += segment_time(
                    prev.dist(pos),
                    self.snow_dist_estimator(pos, prev),
                    direction=pos - prev,
                )
            prev = pos
        return res


# TODO: mutators that use coordinate system rotation (they converge very fast)


@dataclass
class CrazyPathMutator:
    threshold: float

    def mutate(self, path: list[Coordinates], *_) -> list[Coordinates]:
        return [
            Coordinates(uniform(0, 10000), uniform(0, 10000))
            if uniform(0, 1) < self.threshold
            else c
            for c in path
        ]


@dataclass
class WidePathMutator:
    threshold: float
    x_var: float
    y_var: float

    def mutate(self, path: list[Coordinates], *_) -> list[Coordinates]:
        return [
            Coordinates(
                min(max(gauss(c.x, self.x_var), 0), 10000),
                min(max(gauss(c.y, self.y_var), 0), 10000),
            )
            if uniform(0, 1) < self.threshold
            else c
            for c in path
        ]


# TODO: coordinate system aware rand_path_generator (makes convergence faster)


def absolute_rand_path(segmentation, *_):
    res = [None] * segmentation
    for i in range(segmentation):
        res[i] = Coordinates(uniform(0, 10000), uniform(0, 10000))
    return res


# a generalization of just a base path finder
class OptimalPathFinder:
    segmentation: int
    mutate: callable  # context aware
    objective: callable  # context unaware
    rand_path_generator: callable  # context aware
    schedule: dict = {"tmax": 100.0, "tmin": 1, "steps": 340, "updates": 100}

    def __init__(
        self,
        segmentation,
        mutate,
        objective,
        rand_path_generator=None,
        schedule=None,
    ):
        self.segmentation = segmentation
        self.mutate = mutate
        self.objective = objective
        if rand_path_generator is None:
            self.rand_path_generator = absolute_rand_path
        else:
            self.rand_path_generator = rand_path_generator
        if schedule is not None:
            self.schedule = schedule

    def optimal_path(self, f: Coordinates, t: Coordinates) -> Path:
        mutate = self.mutate
        objective = self.objective

        l = f.dist(t)
        if l < 200:
            return Path([f, t], objective([f, t]))

        cos_a = f.x / l
        sin_a = f.y / l

        class PathAnnealer(Annealer):
            def move(self):
                path = [f] + mutate(self.state.path[1:-1], cos_a, sin_a, l) + [t]
                length = objective(path)
                self.state = Path(path, length)

            def energy(self):
                return self.state.length

        init = [f] + self.rand_path_generator(self.segmentation, cos_a, sin_a, l) + [t]
        annealer = PathAnnealer(Path(init, objective(init)))
        annealer.set_schedule(self.schedule)
        best, cost = annealer.anneal()
        linear = Path([f, t], objective([f, t]))
        if cost > linear.length:
            return linear
        # NOTE: assuming int rounding does not change path len significantly
        return Path([Coordinates(int(c.x), int(c.y)) for c in best.path], cost)


def main():
    warnings.filterwarnings("ignore")
    a = Coordinates.from_str(input("Enter a: "))
    b = Coordinates.from_str(input("Enter b: "))
    sengemtation = int(input("Enter number of segments: "))

    sus_map = load_map()
    circles = [Circle.from_snow(s) for s in sus_map.snow_areas]
    snow_dist_calculator = SnowDistEstimator(circles).snow_dist
    objective = CondescendingObjectiveChecker(snow_dist_calculator).objective

    print("linear: ", objective([a, b]))
    # NOTE: yet we use CondescendingObjectiveChecker, but the number of steps is big,
    # so the chance of getting a path with repeated points is low
    best = OptimalPathFinder(
        sengemtation,
        WidePathMutator(1, 3000, 3000).mutate,
        objective,
        schedule={"tmax": 100, "tmin": 1, "steps": 10000, "updates": 500},
    ).optimal_path(a, b)

    print()
    if input("draw? (y/n): ") == "y":
        visualize_route(sus_map, Route(best.path, None, None)).save("data/path.png")


if __name__ == "__main__":
    main()
