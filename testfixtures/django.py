from  __future__ import absolute_import
from functools import partial

from django.db.models import Model
from django.forms import model_to_dict

from .comparison import _compare_mapping, register
from . import compare as base_compare


def compare_model(x, y, context):
    ignore_fields = context.get_option('ignore_fields', set())
    args = []
    for obj in x, y:
        args.append({k: v for (k, v) in model_to_dict(obj).items()
                     if k not in ignore_fields})
    args.append(context)
    args.append(x)
    return _compare_mapping(*args)

register(Model, compare_model)


compare = partial(base_compare, ignore_eq=True)
