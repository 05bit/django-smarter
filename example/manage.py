#!/usr/bin/env python
import os
import sys
from os.path import realpath, dirname, join as joinpath

lib_dir = realpath(joinpath(dirname(__file__), '..'))
if not lib_dir in sys.path:
    sys.path.append(lib_dir)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
