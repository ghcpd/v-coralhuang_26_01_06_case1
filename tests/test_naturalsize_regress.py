from mini_humanize import naturalsize


def test_naturalsize_default_behavior_locked():
    # Lock key outputs to protect against regressions
    assert naturalsize(1536, binary=True, gnu=False, format="%.1f", strip_trailing_zeros=False) == "1.5 KiB"
    assert naturalsize(1000, binary=False, gnu=False, format="%.1f", strip_trailing_zeros=False) == "1.0 kB"
