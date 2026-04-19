"""Root conftest — adds the backend directory to sys.path so pytest can
discover all test modules without manual sys.path hacks."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
