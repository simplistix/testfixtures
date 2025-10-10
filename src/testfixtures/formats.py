"""
Format handlers for serialization and deserialization of common data formats.

This module provides a consistent interface for working with JSON, YAML, and TOML formats.
Each format handler implements the Format protocol with parse() and render() methods.
"""

import json
import tomllib
from types import ModuleType
from typing import Protocol, Any

tomlkit: ModuleType | None
try:
    import tomlkit
except ImportError:
    tomlkit = None

yaml: ModuleType | None
try:
    import yaml
except ImportError:
    yaml = None


class Format(Protocol):
    """
    Protocol for format handlers that can parse and render data.

    This protocol defines the interface for serialization formats used with
    :class:`~testfixtures.TempDirectory`. Implement this protocol to add support
    for additional formats.
    """

    def parse(self, data: str) -> Any:
        """
        Parse a string into a Python object.

        :param data: The string to parse.
        :returns: The deserialized Python object.
        """
        ...

    def render(self, obj: Any) -> str:
        """
        Render a Python object into a string.

        :param obj: The Python object to serialize.
        :returns: The serialized string.
        """
        ...


class JSONFormat:
    """JSON format handler using the standard library json module."""

    def parse(self, data: str) -> Any:
        """Parse JSON string into a Python object."""
        return json.loads(data)

    def render(self, obj: Any) -> str:
        """Render a Python object into a JSON string."""
        return json.dumps(obj)


class YAMLFormat:
    """YAML format handler. Requires pyyaml to be installed."""

    def parse(self, data: str) -> Any:
        """Parse YAML string into a Python object."""
        if yaml is None:
            raise ImportError("YAML support requires pyyaml to be installed")
        return yaml.safe_load(data)

    def render(self, obj: Any) -> str:
        """Render a Python object into a YAML string."""
        if yaml is None:
            raise ImportError("YAML support requires pyyaml to be installed")
        return yaml.safe_dump(obj)


class TOMLFormat:
    """TOML format handler. Read uses stdlib tomllib (3.11+) or tomlkit if available. Write requires tomlkit."""

    def parse(self, data: str) -> Any:
        """Parse TOML string into a Python dict."""
        if tomlkit is not None:
            return tomlkit.loads(data)
        return tomllib.loads(data)

    def render(self, obj: Any) -> str:
        """Render a Python dict into a TOML string."""
        if tomlkit is None:
            raise ImportError("TOML writing requires tomlkit to be installed")
        return tomlkit.dumps(obj)


#: JSON format handler using the standard library. Always available.
JSON: Format = JSONFormat()

#: YAML format handler. Requires the ``pyyaml`` package to be installed.
#:
#: To install the required package, use your package manager to install ``pyyaml``.
YAML: Format = YAMLFormat()

#: TOML format handler. Reading uses the standard library ``tomllib`` module
#: (Python 3.11+) or ``tomlkit`` if available. Writing requires the ``tomlkit``
#: package.
#:
#: To install the package for writing support, use your package manager to install
#: ``tomlkit``, or install testfixtures with the ``toml`` extra.
TOML: Format = TOMLFormat()
