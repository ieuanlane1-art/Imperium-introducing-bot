from config import IBS
from database import get_setting, set_setting, get_active_ibs, add_ib


def ensure_default_ibs():
    active_ibs = get_active_ibs()

    if active_ibs:
        return active_ibs

    for ib in IBS:
        add_ib(ib["name"], ib["username"])

    return get_active_ibs()


def assign_next_ib():
    ibs = ensure_default_ibs()

    if not ibs:
        raise ValueError("No active IBs available")

    current_index = int(get_setting("next_ib_index", "0"))

    # Only reset if the saved index is too high after removing IBs
    if current_index >= len(ibs):
        current_index = len(ibs) - 1

    ib = ibs[current_index]

    next_index = current_index + 1

    if next_index >= len(ibs):
        next_index = 0

    set_setting("next_ib_index", str(next_index))

    return ib