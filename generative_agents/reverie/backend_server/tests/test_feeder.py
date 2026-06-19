import headless


def test_next_env_from_movements_echoes_tiles():
    mv = {"persona": {"A": {"movement": [5, 6]}, "B": {"movement": [7, 8]}}, "meta": {}}
    env = headless.next_env_from_movements(mv)
    assert env == {
        "A": {"maze": "the_ville", "x": 5, "y": 6},
        "B": {"maze": "the_ville", "x": 7, "y": 8},
    }
