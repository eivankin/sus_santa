from collections import defaultdict

from tqdm import tqdm

from constants import MAX_MONEY
from phase3.data import Solution, Map, Present, Gender, Category, Child, Gift
from knapsack import solve
from random import shuffle

from phase3.happiness_estimator import Weights

child_cache = defaultdict(int)


def calc_values_for_knapsack(
        weights: Weights, gift: Gift, children: list[Child]
) -> int:
    max_val = 0
    max_c = None
    for i, c in enumerate(children):
        h = weights.get_gender(c.gender)[c.age][Category(gift.type)](gift.price) // (
                child_cache[i] + 1
        )
        if h > max_val:
            max_val = h
            max_c = i
    child_cache[max_c] += 1
    return max_val


def pass_weights(weights: Weights, func):
    def f(*args, **kwargs):
        return func(weights, *args, **kwargs)

    return f


def most_expensive(
        sorted_gifts: list[Gift],
        children: list[Child],
        shuffle_children=False,
        fit_function=None,
        use_knapsack=False,
        knapsack_value_function=None,
) -> list[Present]:
    presents: list[Present] = []
    if use_knapsack:
        child_cache.clear()
        prices = [g.price for g in sorted_gifts]
        gift_ids = solve(
            [knapsack_value_function(g, children) for g in tqdm(sorted_gifts)],
            [prices],
            [MAX_MONEY],
        )
        remaining_gifts = {sorted_gifts[gid] for gid in gift_ids}
    else:
        remaining_gifts = set(sorted_gifts)

    assert len(remaining_gifts) >= len(children)

    fit_function = fit_function or get_best_fit
    money_so_far = 0
    if shuffle_children:
        shuffle(children)
    for i, child in enumerate(children):
        best = fit_function(
            child,
            remaining_gifts,
            money_so_far,
            0 if use_knapsack else len(children) - i,
        )
        assert best is not None
        money_so_far += best.price
        presents.append(Present(child_id=i, gift_id=best.id))
        remaining_gifts.remove(best)

    return presents


ALL_CATEGORIES = set(Category)

GENDER_TO_CATEGORY: dict[Gender | str, set[Category]] = {
    Gender.MALE: {
        Category.BIKE,
        Category.SOCCER_BALL,
    },
    Gender.FEMALE: {Category.TOY_KITCHEN, Category.CASKET, Category.BATH_TOYS},
}
GENDER_TO_CATEGORY["ANY"] = ALL_CATEGORIES.difference(
    GENDER_TO_CATEGORY[Gender.MALE]
).difference(GENDER_TO_CATEGORY[Gender.FEMALE])

AGES_0_3 = {Category.PAINTS, Category.BATH_TOYS}

AGES_4_6 = ALL_CATEGORIES
AGES_7_10 = ALL_CATEGORIES

AGE_TO_CATEGORY = [AGES_0_3] * 4 + [AGES_4_6] * 3 + [AGES_7_10] * 4
AVG_PRICE = 40


def get_best_fit(
        child: Child, gifts: set[Gift], money_so_far: int, remaining_children: int
) -> Gift:
    for categories in (
            AGE_TO_CATEGORY[child.age].intersection(
                GENDER_TO_CATEGORY[Gender(child.gender)]
            ),
            AGE_TO_CATEGORY[child.age].intersection(GENDER_TO_CATEGORY["ANY"]),
            ALL_CATEGORIES,
    ):
        best_fits = get_by_categories(categories, gifts)
        if not best_fits:
            continue
        filtered = list(filter(
            lambda g: g.price
                      + AVG_PRICE * max(remaining_children - 1, 0)
                      + money_so_far
                      <= MAX_MONEY,
            best_fits,
        ))
        if filtered:
            return max(filtered,
                       key=lambda g: g.price,
                       )


def get_by_categories(categories: set[Category], gifts: set[Gift]) -> list[Gift]:
    return [g for g in gifts if Category(g.type) in categories]


def get_best_fit_with_weights(
        weights: Weights,
        child: Child,
        gifts: set[Gift],
        money_so_far: int,
        remaining_children: int,
):
    return max(
        filter(
            lambda g: g.price
                      + AVG_PRICE * max(remaining_children - 1, 0)
                      + money_so_far
                      <= MAX_MONEY,
            gifts,
        ),
        key=lambda g: weights.get_gender(child.gender)[child.age][Category(g.type)](
            g.price
        ),
    )


def get_sol_cost(m, ps):
    def get_gift(gid: int):
        for g in m.gifts:
            if g.id == gid:
                return g

    return sum(get_gift(p.gift_id).price for p in ps)
