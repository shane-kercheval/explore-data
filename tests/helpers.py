"""Helper functions for unit tests."""

import os


def get_test_file_path(file_path: str) -> str:
    """
    Returns the path to /tests folder, adjusting for the difference in the current working
    directory when debugging vs running from command line.
    """
    return os.path.join(os.getcwd(), 'tests/test_files', file_path)
