from unittest import TestCase

from testfixtures.compat import PY3
from .models import SampleModel
from ..test_compare import CompareHelper
from ... import compare
from ...django import compare as django_compare


class CompareTests(CompareHelper, TestCase):

    def test_simple_same(self):
        django_compare(SampleModel(id=1), SampleModel(id=1))

    def test_simple_diff(self):
        if PY3:
            expected = "'id': 1 != 2"
        else:
            expected = "u'id': 1 != 2"

        self.check_raises(
            SampleModel(id=1), SampleModel(id=2),
            compare=django_compare,
            message=(
                'SampleModel not as expected:\n'
                '\n'
                'same:\n'
                "['value']\n"
                '\n'
                'values differ:\n'+
                expected
            )
        )

    def test_simple_ignore_fields(self):
        django_compare(SampleModel(id=1), SampleModel(id=1),
                       ignore_fields=['id'])

    def test_ignored_because_speshul(self):
        django_compare(SampleModel(not_editable=1), SampleModel(not_editable=2))

    def test_ignored_because_no_longer_speshul(self):
        if PY3:
            same = "['created', 'id', 'value']\n"
        else:
            same = "['created', u'id', 'value']\n"
        self.check_raises(
            SampleModel(not_editable=1), SampleModel(not_editable=2),
            compare=django_compare,
            message=(
                'SampleModel not as expected:\n'
                '\n'
                'same:\n'+
                same+
                '\n'
                'values differ:\n'
                "'not_editable': 1 != 2"
            ),
            non_editable_fields=True
        )

    def test_normal_compare_id_same(self):
        # other diffs ignored
        compare(SampleModel(id=1, value=1), SampleModel(id=1, value=2))

    def test_normal_compare_id_diff(self):
        if PY3:
            expected = (
                "'id': 3 != 4\n"
                "'value': 1 != 2"
            )

        else:
            expected = (
                "'value': 1 != 2\n"
                "u'id': 3 != 4"
            )

        self.check_raises(
            SampleModel(id=3, value=1), SampleModel(id=4, value=2),
            compare=django_compare,
            message=(
                'SampleModel not as expected:\n'
                '\n'
                'values differ:\n'+
                expected
            )
        )
