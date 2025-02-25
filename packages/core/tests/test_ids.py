from flux0_core.ids import gen_id


def test_gen_id_uniqueness() -> None:
    """
    Ensure that gen_id() always generates unique IDs.
    """
    ids = {gen_id() for _ in range(1000)}  # Generate 1000 unique IDs
    assert len(ids) == 1000  # If all are unique, set length should be 1000
