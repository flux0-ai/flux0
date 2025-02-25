from typing import NewType

import nanoid  # type: ignore

UniqueID = NewType("UniqueID", str)


def gen_id() -> UniqueID:
    while True:
        new_id = nanoid.generate(size=10)
        if "-" not in (new_id[0], new_id[-1]) and "_" not in new_id:
            return UniqueID(new_id)
