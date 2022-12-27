import json
import os
from collections import defaultdict

from pyeasyga import pyeasyga
from dataclass_wizard import JSONWizard
from dataclasses import dataclass

from tqdm import tqdm

from phase2.constants import SOLUTIONS_PATH, CACHE_FILE, MIN_AGE, MAX_AGE
from phase2.data import Order, Map, Category, RoundInfo, Gender
from phase2.util import load, load_map, save

from random import randint, randrange

WEIGHTS_PATH = './data/weights.json'


@dataclass
class Function(JSONWizard):
    k: int
    b: int

    def __call__(self, price: int):
        return price * self.k + self.b

    def mutate(self) -> "Function":
        return Function(self.k + randint(-1, 1), self.b + randint(-1, 1))


CategoryToFunction = dict[Category, Function]
AgeToWeights = dict[int, CategoryToFunction]


def ages_to_list(ages: AgeToWeights) -> list[Function]:
    return [ages[age][cat] for age in range(MIN_AGE, MAX_AGE + 1) for cat in Category]


def ages_from_list(funcs: list[Function]) -> AgeToWeights:
    i = 0
    result = defaultdict(dict)
    for age in range(MIN_AGE, MAX_AGE + 1):
        for cat in Category:
            result[age][cat] = funcs[i]
            i += 1

    return result


@dataclass
class Weights(JSONWizard):
    male: AgeToWeights
    female: AgeToWeights

    def to_list(self) -> list[Function]:
        return ages_to_list(self.male) + ages_to_list(self.female)

    @classmethod
    def from_function_list(cls, funcs: list[Function]):
        return cls(
            male=ages_from_list(funcs[: len(funcs) // 2]),
            female=ages_from_list(funcs[len(funcs) // 2:]),
        )

    def get_gender(self, gender: str):
        return self.male if Gender(gender) == Gender.MALE else self.female


def eval_solution(solution: Order, map_data: Map, weights: Weights) -> int:
    happiness = 0
    for present in solution.presenting_gifts:
        child = map_data.children[present.child_id - 1]
        gift = map_data.gifts[present.gift_id - 1]
        happiness += weights.get_gender(child.gender)[child.age][Category(gift.type)](
            gift.price
        )
    return happiness


SolutionData = dict[str, (Order, int)]


def load_all_solutions() -> SolutionData:
    return {
        path.split(".")[0]: (
            load(Order, f"{SOLUTIONS_PATH}{path}"),
            get_score(path.split(".")[0]),
        )
        for path in os.listdir(SOLUTIONS_PATH)
    }


def get_score(round_id: str) -> int:
    with open(CACHE_FILE, "r") as status_cache_file:
        status_cache = json.load(status_cache_file)
    return RoundInfo.from_dict(status_cache[round_id]).data.total_happy


def make_initial_weights() -> AgeToWeights:
    return {
        age: {cat: Function(1, 0) for cat in Category}
        for age in range(MIN_AGE, MAX_AGE + 1)
    }


class FunctionSearcher(pyeasyga.GeneticAlgorithm):
    map_data = load_map()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fitness_function = self.fitness
        self.create_individual = self.new
        self.crossover_function = self.cross
        self.mutate_function = self.mut

    def fitness(self, individual: Weights, data: SolutionData):
        tot_err = 0
        for sol, score in data.values():
            tot_err += abs(eval_solution(sol, self.map_data, individual) - score)
        return tot_err

    @staticmethod
    def new(data: SolutionData):
        if not os.path.exists(WEIGHTS_PATH):
            return Weights(male=make_initial_weights(), female=make_initial_weights())
        return load(Weights, WEIGHTS_PATH)

    def cross(self, parent_1: Weights, parent_2: Weights) -> tuple[Weights, ...]:
        return tuple(
            map(
                Weights.from_function_list,
                self.crossover(parent_1.to_list(), parent_2.to_list()),
            )
        )

    @staticmethod
    def crossover(parent_1, parent_2):
        """Crossover (mate) two parents to produce two children.

        :param parent_1: candidate solution representation (list)
        :param parent_2: candidate solution representation (list)
        :returns: tuple containing two children

        """
        index = randrange(1, len(parent_1))
        child_1 = parent_1[:index] + parent_2[index:]
        child_2 = parent_2[:index] + parent_1[index:]
        return child_1, child_2

    @staticmethod
    def mut(individual: Weights) -> None:
        f_list = individual.to_list()
        mutate_index = randrange(len(f_list))
        f_list[mutate_index] = f_list[mutate_index].mutate()
        new_individual = Weights.from_function_list(f_list)
        individual.male = new_individual.male
        individual.female = new_individual.female

    def run(self):
        """Run (solve) the Genetic Algorithm."""
        self.create_first_generation()

        for i in range(1, self.generations):
            self.create_next_generation()
            curr_best = self.best_individual()
            if curr_best[0] == 0:
                break
            if i % 5 == 0:
                print(f"Generation #{i}, score: {curr_best[0]}")


if __name__ == "__main__":
    sol_data = load_all_solutions()
    ga = FunctionSearcher(
        sol_data,
        population_size=100,
        maximise_fitness=False,
        generations=500,
    )
    ga.run()

    best = ga.best_individual()
    print(best)
    save(best[1], WEIGHTS_PATH)
