# File: tests/unit/conftest.py
"""
pytest configuration for unit tests.
"""
import sys
import types
from pathlib import Path

# Add the collection to the Python path for testing
collection_root = Path(__file__).parent.parent.parent
plugins_path = collection_root / "plugins"
sys.path.insert(0, str(plugins_path))

# Create the ansible_collections namespace if it doesn't exist
if "ansible_collections" not in sys.modules:
    ansible_collections = types.ModuleType("ansible_collections")
    sys.modules["ansible_collections"] = ansible_collections
else:
    ansible_collections = sys.modules["ansible_collections"]

# Create the nested namespace structure
if not hasattr(ansible_collections, "ivorynomad"):
    ansible_collections.ivorynomad = types.ModuleType("ansible_collections.ivorynomad")
    sys.modules["ansible_collections.ivorynomad"] = ansible_collections.ivorynomad

if not hasattr(ansible_collections.ivorynomad, "onepassword"):
    ansible_collections.ivorynomad.onepassword = types.ModuleType(
        "ansible_collections.ivorynomad.onepassword"
    )
    sys.modules["ansible_collections.ivorynomad.onepassword"] = (
        ansible_collections.ivorynomad.onepassword
    )

# Create plugins namespace
if not hasattr(ansible_collections.ivorynomad.onepassword, "plugins"):
    ansible_collections.ivorynomad.onepassword.plugins = types.ModuleType(
        "ansible_collections.ivorynomad.onepassword.plugins"
    )
    sys.modules["ansible_collections.ivorynomad.onepassword.plugins"] = (
        ansible_collections.ivorynomad.onepassword.plugins
    )

if not hasattr(ansible_collections.ivorynomad.onepassword.plugins, "lookup"):
    ansible_collections.ivorynomad.onepassword.plugins.lookup = types.ModuleType(
        "ansible_collections.ivorynomad.onepassword.plugins.lookup"
    )
    sys.modules["ansible_collections.ivorynomad.onepassword.plugins.lookup"] = (
        ansible_collections.ivorynomad.onepassword.plugins.lookup
    )

# Import the plugin module and make it available in the namespace
try:
    from lookup import onepassword

    ansible_collections.ivorynomad.onepassword.plugins.lookup.onepassword = onepassword
    sys.modules[
        "ansible_collections.ivorynomad.onepassword.plugins.lookup.onepassword"
    ] = onepassword
except ImportError as e:
    print(f"Warning: Could not import onepassword plugin: {e}")
    # Create a mock module for testing if the real one can't be imported
    onepassword = types.ModuleType("onepassword")
    ansible_collections.ivorynomad.onepassword.plugins.lookup.onepassword = onepassword
