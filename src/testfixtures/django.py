from typing import TYPE_CHECKING, Any, Iterable, Sequence

from django.db.models import Model, Field

from .comparers import _compare_mapping

if TYPE_CHECKING:
    from .comparing import CompareContext


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


def compare_model(
        x: Model,
        y: Model,
        context: 'CompareContext',
        ignore_fields: Sequence[str] = (),
        non_editable_fields: bool = False,
) -> str | None:
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
    args: Any = []
    for obj in x, y:
        args.append(model_to_dict(obj, ignore_fields, non_editable_fields))
    args.append(context)
    args.append(x)
    return _compare_mapping(*args)
