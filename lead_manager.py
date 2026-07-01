from config import IBS
from database import get_setting, set_setting


def assign_next_ib():
    current_index = int(get_setting("next_ib_index", "0"))

    ib = IBS[current_index]

    next_index = current_index + 1

    if next_index >= len(IBS):
        next_index = 0

    set_setting("next_ib_index", str(next_index))

    return ib
