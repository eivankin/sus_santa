import json
import os
from typing import Optional

from constants import SOLUTIONS_PATH, CACHE_FILE
from data import Order, RoundInfo, Child, Gift
from util import load, load_map


def get_status_from_cache(round_id: str) -> Optional[RoundInfo]:
    with open(CACHE_FILE, "r") as status_cache_file:
        status_cache = json.load(status_cache_file)

    if round_id in status_cache:
        return RoundInfo.from_dict(status_cache[round_id])


dirs = os.listdir(SOLUTIONS_PATH)
for i, filename2 in enumerate(dirs[1:]):
    filename1 = dirs[i]

    print()
    print()
    print(f"Comparing {filename1} and {filename2}...")
    info1 = get_status_from_cache(filename1.split(".")[0])
    info2 = get_status_from_cache(filename2.split(".")[0])
    if info1 is None or info2 is None:
        print("One of the solutions is not in the cache, skipping")
        continue

    order_1: Order = load(Order, SOLUTIONS_PATH + filename1)
    order_2: Order = load(Order, SOLUTIONS_PATH + filename2)
    presents1 = sorted(order_1.presenting_gifts, key=lambda g: g.child_id)
    presents2 = sorted(order_2.presenting_gifts, key=lambda g: g.child_id)

    sus_map = load_map()
    child_map: dict[int, Child] = {c.id: c for c in sus_map.children}
    gift_map: dict[int, Gift] = {g.id: g for g in sus_map.gifts}

    happy_diff = info2.data.total_happy - info1.data.total_happy
    print(f"Change in happiness: {happy_diff}")
    for p1, p2 in zip(presents1, presents2):
        if p1.gift_id != p2.gift_id:
            print()
            child_text = child_map[p1.child_id].compact()
            print(f"WAS: {child_text} -> {gift_map[p1.gift_id].compact()}")
            print(f"NOW: {' ' * len(child_text)} -> {gift_map[p2.gift_id].compact()}")
