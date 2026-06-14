"""
conftest.py — pytest configuration for Telecom Integration Infrastructure Lab.

Adds the project root to sys.path so that test files can import from
`scripts/` without installing the package.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
