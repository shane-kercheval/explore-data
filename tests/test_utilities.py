"""Test utilities.py."""

from source.library.utilities import split_list


def test__split_list() -> None:
    """Test that the `split_list` function correctly splits list into sublists."""
    assert split_list(items=[], n_groups=3) == [[], [], []]
    assert split_list(items=[10], n_groups=3) == [[10], [], []]
    assert split_list(items=[1, 2, 3], n_groups=3) == [[1], [2], [3]]
    assert split_list(items=[1, 2, 3, 4, 5], n_groups=3) == [[1, 2], [3, 4], [5]]
    assert split_list(items=[1, 2, 3, 4, 5, 6], n_groups=3) == [[1, 2], [3, 4], [5, 6]]
    assert split_list(items=[1, 2, 3, 4, 5, 6, 7], n_groups=3) == [[1, 2, 3], [4, 5], [6, 7]]
    assert split_list(items=[1, 2, 3, 4, 5, 6, 7, 8], n_groups=3) == [[1, 2, 3], [4, 5, 6], [7, 8]]
    assert split_list(items=[1, 2, 3, 4, 5, 6, 7, 8, 9], n_groups=3) == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]  # noqa
