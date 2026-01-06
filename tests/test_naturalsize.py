from mini_humanize import naturalsize


def test_naturalsize_regression_trailing_zero():
    # Regression protection: default formatting must keep the trailing zero
    assert (
        naturalsize(1000, binary=False, gnu=False, format="%.1f", strip_trailing_zeros=False)
        == "1.0 kB"
    )


def test_naturalsize_binary_and_gnu():
    assert naturalsize(1536, binary=True) == "1.5 KiB"
    assert naturalsize(1000, gnu=True) == "1.0K"


def test_strip_trailing_zeros_removes_dot_zero():
    assert naturalsize(1024, binary=True, format="%.1f", strip_trailing_zeros=True) == "1 KiB"
