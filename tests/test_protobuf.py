import pytest

pytest.importorskip("google.protobuf")

from google.protobuf import descriptor_pool, message_factory
from google.protobuf.descriptor_pb2 import (
    DescriptorProto,
    FieldDescriptorProto,
    FieldOptions,
    FileDescriptorProto,
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


def int32_field(name, number, **kw):
    return FieldDescriptorProto(
        name=name,
        number=number,
        type=FieldDescriptorProto.TYPE_INT32,
        label=FieldDescriptorProto.LABEL_OPTIONAL,
        **kw,
    )


def extendable_with_extension():
    # A proto2 message with a field and an extension that are both named "value":
    pool = descriptor_pool.DescriptorPool()
    pool.AddSerializedFile(FileDescriptorProto(
        name="testfixtures_extensions.proto",
        package="testfixtures.test",
        syntax="proto2",
        message_type=[DescriptorProto(
            name="Extendable",
            field=[int32_field("value", 1)],
            extension_range=[DescriptorProto.ExtensionRange(start=100, end=200)],
        )],
        extension=[int32_field("value", 100, extendee=".testfixtures.test.Extendable")],
    ).SerializeToString())
    message_type = pool.FindMessageTypeByName("testfixtures.test.Extendable")
    return (
        message_factory.GetMessageClass(message_type),
        pool.FindExtensionByName("testfixtures.test.value"),
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
    # The type of map containers differs between protobuf's implementations:
    map_type = type(Struct().fields).__name__
    with ShouldAssert(
        "Struct not as expected:\n"
        "\n"
        "attributes differ:\n"
        "'fields': {'a': string_value: \"y\"\n"
        "} (expected) != {'a': string_value: \"x\"\n"
        "} (actual)\n"
        "\n"
        f"While comparing .fields: {map_type} not as expected:\n"
        "\n"
        "values differ:\n"
        "'a': string_value: \"y\"\n"
        " (expected) != string_value: \"x\"\n"
        " (actual)\n"
        "\n"
        "While comparing .fields['a']: Value not as expected:\n"
        "\n"
        "attributes differ:\n"
        "'string_value': 'y' (expected) != 'x' (actual)\n"
        "\n"
        "While comparing .fields['a'].string_value: 'y' (expected) != 'x' (actual)"
    ):
        compare(
            Struct(fields={"a": Value(string_value="x")}),
            expected=Struct(fields={"a": Value(string_value="y")}),
        )


def test_extension_named_like_a_field():
    Extendable, value_extension = extendable_with_extension()
    actual = Extendable(value=1)
    actual.Extensions[value_extension] = 3
    expected = Extendable(value=2)
    expected.Extensions[value_extension] = 3
    with ShouldAssert(
        "Extendable not as expected:\n"
        "\n"
        "attributes same:\n"
        "['[testfixtures.test.value]']\n"
        "\n"
        "attributes differ:\n"
        "'value': 2 (expected) != 1 (actual)"
    ):
        compare(actual, expected=expected)


def test_comparer_for_extension_value_is_used():
    def compare_ignoring_ints(x, y, context):
        return None

    Extendable, value_extension = extendable_with_extension()
    actual = Extendable()
    actual.Extensions[value_extension] = 3
    expected = Extendable()
    expected.Extensions[value_extension] = 4
    compare(actual, expected=expected, comparers={int: compare_ignoring_ints})


def test_comparer_for_nested_message_type_is_used():
    def compare_ignoring_options(x, y, context):
        return None

    compare(
        DescriptorProto(name="M", options=MessageOptions(deprecated=True)),
        expected=DescriptorProto(name="M", options=MessageOptions(deprecated=False)),
        comparers={MessageOptions: compare_ignoring_options},
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
        "Both expected and actual have the same field values, but their unknown fields differ!"
    ):
        compare(actual, expected=Timestamp(seconds=1))
