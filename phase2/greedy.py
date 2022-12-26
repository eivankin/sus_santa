from constants import MAX_MONEY
from phase2.data import Order, Map, Present, Gender, Category, Child, Gift
from knapsack import solve


def most_expensive(map_data: Map) -> list[Present]:
    values = [g.price for g in map_data.gifts]
    gift_ids = solve(
        values,
        [values],
        [MAX_MONEY]
    )
    presents: list[Present] = []
    remaining_gifts = {
        map_data.gifts[gid] for gid in gift_ids
    }
    for child in map_data.children:
        best = get_best_fit(child, remaining_gifts)
        presents.append(Present(child_id=child.id, gift_id=best.id))
        remaining_gifts.remove(best)

    return presents


ALL_CATEGORIES = {Category.CONSTRUCTORS, Category.RADIO_CONTROLLED_TOYS, Category.TOY_VEHICLES,
                  Category.COMPUTER_GAMES, Category.BOARD_GAMES, Category.DOLLS, Category.SOFT_TOYS,
                  Category.CLOTHES, Category.OUTDOOR_GAMES, Category.PLAYGROUND, Category.PET,
                  Category.SWEETS, Category.BOOKS}

GENDER_TO_CATEGORY: dict[Gender | str, set[Category]] = {
    Gender.MALE: {
        Category.CONSTRUCTORS, Category.RADIO_CONTROLLED_TOYS, Category.TOY_VEHICLES,
        Category.COMPUTER_GAMES, Category.BOARD_GAMES
    },
    Gender.FEMALE: {
        Category.DOLLS, Category.SOFT_TOYS, Category.CLOTHES
    },
}
GENDER_TO_CATEGORY['ANY'] = ALL_CATEGORIES.difference(
    GENDER_TO_CATEGORY[Gender.MALE]).difference(GENDER_TO_CATEGORY[Gender.FEMALE])

AGES_0_3 = {
    Category.SOFT_TOYS, Category.PLAYGROUND, Category.TOY_VEHICLES
}

AGES_4_6 = AGES_0_3.union({
    Category.DOLLS, Category.CONSTRUCTORS, Category.RADIO_CONTROLLED_TOYS,
    Category.OUTDOOR_GAMES, Category.SWEETS, Category.PET, Category.CLOTHES
})
AGES_7_10 = ALL_CATEGORIES

AGE_TO_CATEGORY = [AGES_0_3] * 4 + [AGES_4_6] * 3 + [AGES_7_10] * 4


def get_best_fit(child: Child, gifts: set[Gift]) -> Gift:
    for categories in (
            AGE_TO_CATEGORY[child.age].intersection(GENDER_TO_CATEGORY[Gender(child.gender)]),
            AGE_TO_CATEGORY[child.age].intersection(GENDER_TO_CATEGORY['ANY']),
            ALL_CATEGORIES
    ):
        best_fits = get_by_categories(categories, gifts)
        if not best_fits:
            continue
        return max(best_fits, key=lambda g: g.price)


def get_by_categories(categories: set[Category], gifts: set[Gift]) -> list[Gift]:
    return [g for g in gifts if Category(g.type) in categories]
