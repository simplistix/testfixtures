from typing import Any

import pytest

from testfixtures import compare, ShouldRaise, Replacer
from testfixtures import formats
from testfixtures.formats import JSON, YAML, TOML


class TestJSON:

    def test_parse_dict(self) -> None:
        result = JSON.parse('{"key": "value", "num": 42}')
        compare(result, expected={"key": "value", "num": 42})

    def test_parse_list(self) -> None:
        result = JSON.parse('[1, 2, 3]')
        compare(result, expected=[1, 2, 3])

    def test_parse_nested(self) -> None:
        result = JSON.parse('{"outer": {"inner": "value"}}')
        compare(result, expected={"outer": {"inner": "value"}})

    def test_render_dict(self) -> None:
        result = JSON.render({"key": "value", "num": 42})
        compare(result, expected='{"key": "value", "num": 42}')

    def test_render_list(self) -> None:
        result = JSON.render([1, 2, 3])
        compare(result, expected='[1, 2, 3]')

    def test_roundtrip(self) -> None:
        original: dict[str, Any] = {"a": 1, "b": [2, 3], "c": {"d": "e"}}
        serialized = JSON.render(original)
        deserialized = JSON.parse(serialized)
        compare(deserialized, expected=original)

    def test_typed_annotation(self) -> None:
        data: dict[str, str] = {"key": "value"}
        serialized: str = JSON.render(data)
        deserialized: dict[str, str] = JSON.parse(serialized)
        compare(deserialized, expected=data)


class TestYAML:

    def test_parse_dict(self) -> None:
        pytest.importorskip("yaml")
        result = YAML.parse('key: value\nnum: 42\n')
        compare(result, expected={"key": "value", "num": 42})

    def test_parse_list(self) -> None:
        pytest.importorskip("yaml")
        result = YAML.parse('- 1\n- 2\n- 3\n')
        compare(result, expected=[1, 2, 3])

    def test_render_dict(self) -> None:
        pytest.importorskip("yaml")
        result = YAML.render({"key": "value", "num": 42})
        compare(result, expected='key: value\nnum: 42\n')

    def test_roundtrip(self) -> None:
        pytest.importorskip("yaml")
        original: dict[str, Any] = {"a": 1, "b": [2, 3], "c": {"d": "e"}}
        serialized = YAML.render(original)
        deserialized = YAML.parse(serialized)
        compare(deserialized, expected=original)

    def test_typed_annotation(self) -> None:
        pytest.importorskip("yaml")
        data: list[str] = ["foo", "bar", "baz"]
        serialized: str = YAML.render(data)
        deserialized: list[str] = YAML.parse(serialized)
        compare(deserialized, expected=data)

    def test_missing_pyyaml_parse(self) -> None:
        with (
            Replacer() as r,
            ShouldRaise(ImportError("YAML support requires pyyaml to be installed"))
        ):
            r.replace('.yaml', None, container=formats)
            YAML.parse('key: value\n')

    def test_missing_pyyaml_render(self) -> None:
        with (
            Replacer() as r,
            ShouldRaise(ImportError("YAML support requires pyyaml to be installed"))
        ):
            r.replace('.yaml', None, container=formats)
            YAML.render({"key": "value"})


class TestTOML:

    def test_parse_dict(self) -> None:
        result = TOML.parse('key = "value"\nnum = 42\n')
        compare(result, expected={"key": "value", "num": 42})

    def test_parse_nested(self) -> None:
        result = TOML.parse('[section]\nkey = "value"\n')
        compare(result, expected={"section": {"key": "value"}})

    def test_parse_array(self) -> None:
        result = TOML.parse('items = [1, 2, 3]\n')
        compare(result, expected={"items": [1, 2, 3]})

    def test_render_dict(self) -> None:
        pytest.importorskip("tomlkit")
        result = TOML.render({"key": "value", "num": 42})
        compare(result, expected='key = "value"\nnum = 42\n')

    def test_roundtrip(self) -> None:
        pytest.importorskip("tomlkit")
        original: dict[str, Any] = {"a": 1, "b": [2, 3], "c": {"d": "e"}}
        serialized = TOML.render(original)
        deserialized = TOML.parse(serialized)
        compare(deserialized, expected=original)

    def test_typed_annotation(self) -> None:
        pytest.importorskip("tomlkit")
        data: dict[str, int] = {"num": 42}
        serialized: str = TOML.render(data)
        deserialized: dict[str, int] = TOML.parse(serialized)
        compare(deserialized, expected=data)

    def test_missing_tomlkit_render(self) -> None:
        with (
            Replacer() as r,
            ShouldRaise(ImportError('TOML writing requires tomlkit to be installed'))
        ):
            r.replace('.tomlkit', None, container=formats)
            TOML.render({"key": "value"})
