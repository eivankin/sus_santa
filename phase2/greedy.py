from tqdm import tqdm

from constants import MAX_MONEY
from phase2.data import Order, Map, Present, Gender, Category, Child, Gift
from knapsack import solve
from random import shuffle

from phase2.happiness_estimator import Weights


def calc_values_for_knapsack(weights: Weights, gift: Gift, map_data: Map):
    return max(weights.get_gender(c.gender)[c.age][Category(gift.type)](gift.price)
               for c in map_data.children)


def pass_weights(weights: Weights, func):
    def f(*args, **kwargs):
        return func(weights, *args, **kwargs)

    return f


def most_expensive(
        map_data: Map, shuffle_children=False, fit_function=None, use_knapsack=False,
        knapsack_value_function=None
) -> list[Present]:
    presents: list[Present] = []
    if use_knapsack:
        prices = [g.price for g in map_data.gifts]
        gift_ids = solve(
            prices,
            [[knapsack_value_function(g, map_data) for g in tqdm(map_data.gifts)]],
            [MAX_MONEY]
        )
        remaining_gifts = {
            map_data.gifts[gid] for gid in gift_ids
        }
    else:
        remaining_gifts = set(map_data.gifts)

    fit_function = fit_function or get_best_fit
    money_so_far = 0
    if shuffle_children:
        shuffle(map_data.children)
    for i, child in enumerate(map_data.children):
        best = fit_function(
            child, remaining_gifts, money_so_far, 0 if use_knapsack else len(map_data.children) - i
        )
        money_so_far += best.price
        presents.append(Present(child_id=child.id, gift_id=best.id))
        remaining_gifts.remove(best)

    return presents


ALL_CATEGORIES = {
    Category.CONSTRUCTORS,
    Category.RADIO_CONTROLLED_TOYS,
    Category.TOY_VEHICLES,
    Category.COMPUTER_GAMES,
    Category.BOARD_GAMES,
    Category.DOLLS,
    Category.SOFT_TOYS,
    Category.CLOTHES,
    Category.OUTDOOR_GAMES,
    Category.PLAYGROUND,
    Category.PET,
    Category.SWEETS,
    Category.BOOKS,
}

GENDER_TO_CATEGORY: dict[Gender | str, set[Category]] = {
    Gender.MALE: {
        Category.CONSTRUCTORS,
        Category.RADIO_CONTROLLED_TOYS,
        Category.TOY_VEHICLES,
        Category.COMPUTER_GAMES,
        Category.BOARD_GAMES,
    },
    Gender.FEMALE: {Category.DOLLS, Category.SOFT_TOYS, Category.CLOTHES},
}
GENDER_TO_CATEGORY["ANY"] = ALL_CATEGORIES.difference(
    GENDER_TO_CATEGORY[Gender.MALE]
).difference(GENDER_TO_CATEGORY[Gender.FEMALE])

AGES_0_3 = {Category.SOFT_TOYS, Category.PLAYGROUND, Category.TOY_VEHICLES}

AGES_4_6 = AGES_0_3.union(
    {
        Category.DOLLS,
        Category.CONSTRUCTORS,
        Category.RADIO_CONTROLLED_TOYS,
        Category.OUTDOOR_GAMES,
        Category.SWEETS,
        Category.PET,
        Category.CLOTHES,
    }
)
AGES_7_10 = ALL_CATEGORIES

AGE_TO_CATEGORY = [AGES_0_3] * 4 + [AGES_4_6] * 3 + [AGES_7_10] * 4
AVG_PRICE = 90


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
        return max(
            filter(
                lambda g: g.price + AVG_PRICE * (remaining_children - 1) + money_so_far
                          <= MAX_MONEY,
                best_fits,
            ),
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
            lambda g: g.price + AVG_PRICE * (remaining_children - 1) + money_so_far
                      <= MAX_MONEY,
            gifts,
        ),
        key=lambda g: weights.get_gender(child.gender)[child.age][Category(g.type)](
            g.price
        ),
    )
