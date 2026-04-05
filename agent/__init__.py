"""
ServerRoot.net Agent Package
Ensures correct module paths for all submodules
"""
import sys
import os

# Ensure workspace root is always in path
_workspace = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _workspace not in sys.path:
    sys.path.insert(0, _workspace)