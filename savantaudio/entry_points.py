"""
savantaudio.entry_points.py
~~~~~~~~~~~~~~~~~~~~~~

This module contains the entry-point functions for the savantaudio module,
that are referenced in setup.py.
"""

from os import remove
from sys import argv

import requests


def main() -> None:
    """Main package entry point.

    Delegates to other functions based on user input.
    """

    try:
        user_cmd = argv[1]
        if user_cmd == 'install':
            pass
        else:
            RuntimeError('please supply a command for savantaudio - e.g. install.')
    except IndexError:
        RuntimeError('please supply a command for savantaudio - e.g. install.')
    return None
