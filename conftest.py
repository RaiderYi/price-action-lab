"""Root conftest: make flat legacy modules in src/ importable for tests.

S0-03/S0-04: single canonical path setup. Test files no longer need their own
sys.path hacks; integration tests under tests/integration are excluded by
default (pyproject addopts) and only run with private modules available.
"""
import os
import sys

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)
