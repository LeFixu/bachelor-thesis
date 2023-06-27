"""
This module contains the function get_location_of_file
"""

from os import path


def get_location_of_file(file: str) -> str:
    """
    Get the relative path to the given file
    """
    # Many thanks to https://www.delftstack.com/howto/python/python-get-path/
    return path.dirname(path.relpath(file))
