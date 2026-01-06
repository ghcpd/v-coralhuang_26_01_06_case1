from mini_humanize import naturalsize, parse_size


def test_trailing_zero_regression():
    # Ensure default behavior doesn't strip trailing zeros
    assert naturalsize(1000) == "1.0 kB"
    assert naturalsize(1000, strip_trailing_zeros=True) == "1 kB"


def test_round_trip_with_gnu_and_binary():
    # If we format with gnu and binary, parsing with matching defaults should round-trip
    s = naturalsize(1536, binary=True, gnu=True, format="%.1f", strip_trailing_zeros=False)
    # s should be something like '1.5K' (no space)
    assert parse_size(s, default_gnu=True, default_binary=True, strict=False) == 1536


def test_underscore_thousands_separator():
    assert parse_size("1_234 kB", allow_thousands_separator=True) == 1234_000
