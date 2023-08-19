"""Misc utilities."""


def split_list(items: list, n_groups: int) -> list[list]:
    """
    Splits a list of items into n groups.

    Args:
        items (list): The list of items to split.
        n_groups (int): The number of groups to split the items into.

    Returns:
        list[list]: A list of n sublists, where each sublist contains an equal number of items from
        the original list.

    Examples:
        >>> split_list([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 3)
        [[1, 2, 3, 4], [5, 6, 7], [8, 9, 10]]

        >>> split_list([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 4)
        [[1, 2, 3], [4, 5, 6], [7, 8], [9, 10]]

        >>> split_list([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 1)
        [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]

        >>> split_list([], 3)
        [[], [], []]
    """
    k, m = divmod(len(items), n_groups)
    return [items[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n_groups)]
