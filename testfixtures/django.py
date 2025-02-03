from typing import Any, Sequence, Iterable

from django.db.models import Model, Field

from . import compare as base_compare
from .comparison import _compare_mapping, register, CompareContext, unspecified, Registry


def instance_fields(instance: Model) -> Iterable[Field]:
    opts = instance._meta
    for name in (
        'concrete_fields',
        'virtual_fields',
        'private_fields',
    ):
        fields = getattr(opts, name, None)
        if fields:
            for field in fields:
                yield field


def model_to_dict(
        instance: Model,
        exclude: Sequence[str],
        include_not_editable: bool,
) -> dict[str, Any]:
    data = {}
    for f in instance_fields(instance):
        if f.name in exclude:
            continue
        if not getattr(f, 'editable', False) and not include_not_editable:
            continue
        data[f.name] = f.value_from_object(instance)
    return data


def compare_model(x: Model, y: Model, context: CompareContext) -> str | None:
    """
    Returns an informative string describing the differences between the two
    supplied Django model instances. The way in which this comparison is
    performed can be controlled using the following parameters:

    :param ignore_fields:
      A sequence of fields to ignore during comparison, most commonly
      set to ``['id']``. By default, no fields are ignored.

    :param non_editable_fields:
      If `True`, then fields with ``editable=False`` will be included in the
      comparison. By default, these fields are ignored.
    """
    ignore_fields = context.get_option('ignore_fields', set())
    non_editable_fields= context.get_option('non_editable_fields', False)
    args: Any = []
    for obj in x, y:
        args.append(model_to_dict(obj, ignore_fields, non_editable_fields))
    args.append(context)
    args.append(x)
    return _compare_mapping(*args)


register(Model, compare_model)


def compare(
        *args: Any,
        x: Any = unspecified,
        y: Any = unspecified,
        expected: Any = unspecified,
        actual: Any = unspecified,
        prefix: str | None = None,
        suffix: str | None = None,
        x_label: str | None = None,
        y_label: str | None = None,
        raises: bool = True,
        recursive: bool = True,
        strict: bool = False,
        ignore_eq: bool = True,
        comparers: Registry | None = None,
        **options: Any
) -> str | None:
    """
    This is identical to :func:`~testfixtures.compare`, but with ``ignore=True``
    automatically set to make comparing django :class:`~django.db.models.Model`
    instances easier.
    """
    return base_compare(
        *args,
        x=x,
        y=y,
        expected=expected,
        actual=actual,
        prefix=prefix,
        suffix=suffix,
        x_label=x_label,
        y_label=y_label,
        raises=raises,
        recursive=recursive,
        strict=strict,
        ignore_eq=ignore_eq,
        comparers=comparers,
        **options
    )
