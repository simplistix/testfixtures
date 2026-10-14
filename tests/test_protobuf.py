import pytest

pytest.importorskip("google.protobuf")

from google.protobuf.descriptor_pb2 import (
    DescriptorProto,
    FieldDescriptorProto,
    FieldOptions,
    MessageOptions,
)
from google.protobuf.duration_pb2 import Duration
from google.protobuf.field_mask_pb2 import FieldMask
from google.protobuf.struct_pb2 import Struct, Value
from google.protobuf.timestamp_pb2 import Timestamp

import testfixtures.protobuf
from testfixtures import ShouldAssert, compare

COMPARE_OPTIONS = pytest.mark.parametrize(
    "options",
    [{}, {"strict": True}, {"ignore_eq": True}, {"strict": True, "ignore_eq": True}],
)


def test_importable():
    compare(testfixtures.protobuf.protobuf.__name__, expected="google.protobuf")


@COMPARE_OPTIONS
def test_equal_messages(options):
    compare(Timestamp(seconds=1), expected=Timestamp(seconds=1), **options)


@COMPARE_OPTIONS
def test_unequal_messages(options):
    with ShouldAssert(
        "Timestamp not as expected:\n"
        "\n"
        "attributes differ:\n"
        "'seconds': 2 (expected) != 1 (actual)"
    ):
        compare(Timestamp(seconds=1), expected=Timestamp(seconds=2), **options)


def test_unequal_messages_in_dict_breadcrumb():
    with ShouldAssert(
        "dict not as expected:\n"
        "\n"
        "values differ:\n"
        "'foo': seconds: 2\n"
        " (expected) != seconds: 1\n"
        " (actual)\n"
        "\n"
        "While comparing ['foo']: Timestamp not as expected:\n"
        "\n"
        "attributes differ:\n"
        "'seconds': 2 (expected) != 1 (actual)"
    ):
        compare({"foo": Timestamp(seconds=1)}, expected={"foo": Timestamp(seconds=2)})


def test_messages_of_different_types():
    with ShouldAssert(
        "seconds: 1\n"
        " (<class 'google.protobuf.duration_pb2.Duration'>) (expected) != seconds: 1\n"
        " (<class 'google.protobuf.timestamp_pb2.Timestamp'>) (actual)"
    ):
        compare(Timestamp(seconds=1), expected=Duration(seconds=1))


def test_nested_messages():
    with ShouldAssert(
        "DescriptorProto not as expected:\n"
        "\n"
        "attributes same:\n"
        "['name']\n"
        "\n"
        "attributes differ:\n"
        "'options': deprecated: false\n"
        " (expected) != deprecated: true\n"
        " (actual)\n"
        "\n"
        "While comparing .options: MessageOptions not as expected:\n"
        "\n"
        "attributes differ:\n"
        "'deprecated': False (expected) != True (actual)"
    ):
        compare(
            DescriptorProto(name="M", options=MessageOptions(deprecated=True)),
            expected=DescriptorProto(name="M", options=MessageOptions(deprecated=False)),
        )


def test_sibling_nested_messages_both_reported():
    with ShouldAssert(
        "DescriptorProto not as expected:\n"
        "\n"
        "attributes differ:\n"
        "'extension': [options {\n"
        "  deprecated: false\n"
        "}\n"
        "] (expected) != [options {\n"
        "  deprecated: true\n"
        "}\n"
        "] (actual)\n"
        "'field': [options {\n"
        "  deprecated: false\n"
        "}\n"
        "] (expected) != [options {\n"
        "  deprecated: true\n"
        "}\n"
        "] (actual)\n"
        "\n"
        "While comparing .extension: sequence not as expected:\n"
        "\n"
        "same:\n"
        "()\n"
        "\n"
        "expected:\n"
        "(options {\n"
        "  deprecated: false\n"
        "}\n"
        ",)\n"
        "\n"
        "actual:\n"
        "(options {\n"
        "  deprecated: true\n"
        "}\n"
        ",)\n"
        "\n"
        "While comparing .extension[0]: FieldDescriptorProto not as expected:\n"
        "\n"
        "attributes differ:\n"
        "'options': deprecated: false\n"
        " (expected) != deprecated: true\n"
        " (actual)\n"
        "\n"
        "While comparing .extension[0].options: FieldOptions not as expected:\n"
        "\n"
        "attributes differ:\n"
        "'deprecated': False (expected) != True (actual)\n"
        "\n"
        "While comparing .field: sequence not as expected:\n"
        "\n"
        "same:\n"
        "()\n"
        "\n"
        "expected:\n"
        "(options {\n"
        "  deprecated: false\n"
        "}\n"
        ",)\n"
        "\n"
        "actual:\n"
        "(options {\n"
        "  deprecated: true\n"
        "}\n"
        ",)\n"
        "\n"
        "While comparing .field[0]: FieldDescriptorProto not as expected:\n"
        "\n"
        "attributes differ:\n"
        "'options': deprecated: false\n"
        " (expected) != deprecated: true\n"
        " (actual)\n"
        "\n"
        "While comparing .field[0].options: FieldOptions not as expected:\n"
        "\n"
        "attributes differ:\n"
        "'deprecated': False (expected) != True (actual)"
    ):
        def descriptor(deprecated):
            return DescriptorProto(
                field=[FieldDescriptorProto(options=FieldOptions(deprecated=deprecated))],
                extension=[FieldDescriptorProto(options=FieldOptions(deprecated=deprecated))],
            )

        compare(descriptor(True), expected=descriptor(False))


def test_repeated_scalar_field():
    with ShouldAssert(
        "FieldMask not as expected:\n"
        "\n"
        "attributes differ:\n"
        "'paths': ['a', 'c'] (expected) != ['a', 'b'] (actual)\n"
        "\n"
        "While comparing .paths: sequence not as expected:\n"
        "\n"
        "same:\n"
        "('a',)\n"
        "\n"
        "expected:\n"
        "('c',)\n"
        "\n"
        "actual:\n"
        "('b',)\n"
        "\n"
        "While comparing .paths[1]: 'c' (expected) != 'b' (actual)"
    ):
        compare(FieldMask(paths=["a", "b"]), expected=FieldMask(paths=["a", "c"]))


def test_repeated_message_field():
    with ShouldAssert(
        "DescriptorProto not as expected:\n"
        "\n"
        "attributes differ:\n"
        "'field': [name: \"a\"\n"
        "number: 2\n"
        "] (expected) != [name: \"a\"\n"
        "number: 1\n"
        "] (actual)\n"
        "\n"
        "While comparing .field: sequence not as expected:\n"
        "\n"
        "same:\n"
        "()\n"
        "\n"
        "expected:\n"
        "(name: \"a\"\n"
        "number: 2\n"
        ",)\n"
        "\n"
        "actual:\n"
        "(name: \"a\"\n"
        "number: 1\n"
        ",)\n"
        "\n"
        "While comparing .field[0]: FieldDescriptorProto not as expected:\n"
        "\n"
        "attributes same:\n"
        "['name']\n"
        "\n"
        "attributes differ:\n"
        "'number': 2 (expected) != 1 (actual)"
    ):
        compare(
            DescriptorProto(field=[FieldDescriptorProto(name="a", number=1)]),
            expected=DescriptorProto(field=[FieldDescriptorProto(name="a", number=2)]),
        )


def test_map_field():
    with ShouldAssert(
        "Struct not as expected:\n"
        "\n"
        "attributes differ:\n"
        "'fields': {'a': number_value: 2\n"
        "} (expected) != {'a': number_value: 1\n"
        "} (actual)\n"
        "\n"
        "While comparing .fields: MessageMapContainer not as expected:\n"
        "\n"
        "values differ:\n"
        "'a': number_value: 2\n"
        " (expected) != number_value: 1\n"
        " (actual)\n"
        "\n"
        "While comparing .fields['a']: Value not as expected:\n"
        "\n"
        "attributes differ:\n"
        "'number_value': 2.0 (expected) != 1.0 (actual)"
    ):
        compare(
            Struct(fields={"a": Value(number_value=1)}),
            expected=Struct(fields={"a": Value(number_value=2)}),
        )


@COMPARE_OPTIONS
def test_field_without_presence_set_to_default(options):
    compare(Timestamp(seconds=0), expected=Timestamp(), **options)


def test_field_with_presence_set_to_default():
    with ShouldAssert(
        "FieldDescriptorProto not as expected:\n"
        "\n"
        "attributes in actual but not expected:\n"
        "'name': ''"
    ):
        compare(FieldDescriptorProto(name=""), expected=FieldDescriptorProto())


def test_oneof_member_set_to_default():
    with ShouldAssert(
        "Value not as expected:\n"
        "\n"
        "attributes in actual but not expected:\n"
        "'number_value': 0.0"
    ):
        compare(Value(number_value=0), expected=Value())


def test_only_unknown_fields_differ():
    actual = Timestamp()
    # Field 3 does not exist on Timestamp, so this is kept as an unknown field:
    actual.ParseFromString(Timestamp(seconds=1).SerializeToString() + b"\x18\x05")
    with ShouldAssert(
        "Both expected and actual have the same field values, but are not equal!"
    ):
        compare(actual, expected=Timestamp(seconds=1))
