from importlib import import_module
from typing import Optional


def _optional_import(module_name: str) -> Optional[object]:
    """Try to import a module and return it if available, else return None."""
    try:
        return import_module(module_name)
    except ImportError:
        return None


# Lazy-load optional integrations
langchain = _optional_import("flux0_stream.frameworks.langchain")

__all__ = ["langchain"]
