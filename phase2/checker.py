from phase2.data import Order, Map
from constants import MAX_MONEY


def validate(solution: Order, map_data: Map):
    assert len(solution.presenting_gifts) == len(map_data.children)
    gifts = {g.id for g in map_data.gifts}
    children = {c.id for c in map_data.children}
    money_so_far = 0
    for present in solution.presenting_gifts:
        assert present.gift_id in gifts
        assert present.child_id in children
        money_so_far += map_data.gifts[present.gift_id - 1].price

    assert money_so_far <= MAX_MONEY, f"{money_so_far}"
