from unittest import TestCase

import pytest
from django.contrib.auth.models import User
from testfixtures import OutputCapture, Replacer
from testfixtures.comparing import registry
from .models import SampleModel
from tests.test_django.manage import main

from tests.test_compare import CompareHelper
from testfixtures import compare


class CompareTests(CompareHelper, TestCase):

    def test_simple_same(self):
        compare(SampleModel(id=1), SampleModel(id=1))

    def test_simple_diff(self):
        self.check_raises(
            SampleModel(id=1), SampleModel(id=2),
            message=(
                'SampleModel not as expected:\n'
                '\n'
                'same:\n'
                "['value']\n"
                '\n'
                'values differ:\n'
                "'id': 1 != 2"
            )
        )

    def test_simple_ignore_fields(self):
        compare(SampleModel(id=1), SampleModel(id=1), ignore_fields=['id'])

    def test_ignored_because_speshul(self):
        compare(SampleModel(not_editable=1), SampleModel(not_editable=2))

    def test_ignored_because_no_longer_speshul(self):
        self.check_raises(
            SampleModel(not_editable=1), SampleModel(not_editable=2),
            message=(
                'SampleModel not as expected:\n'
                '\n'
                'same:\n'
                "['created', 'id', 'value']\n"
                '\n'
                'values differ:\n'
                "'not_editable': 1 != 2"
            ),
            non_editable_fields=True
        )

    def test_normal_compare_id_same(self):
        # without the comparer registered, the models compare equal:
        with registry():
            compare(SampleModel(id=1, value=1), SampleModel(id=1, value=2))

    def test_normal_compare_id_diff(self):
        self.check_raises(
            SampleModel(id=3, value=1), SampleModel(id=4, value=2),
            message=(
                'SampleModel not as expected:\n'
                '\n'
                'values differ:\n'
                "'id': 3 != 4\n"
                "'value': 1 != 2"
            )
        )

    def test_manage(self):
        with OutputCapture() as output:
            with Replacer() as r:
                r.replace('os.environ.DJANGO_SETTINGS_MODULE', '', strict=False)
                r.replace('sys.argv', ['x', 'check'])
                main()
        output.compare('System check identified no issues (0 silenced).')

    @pytest.mark.django_db
    def test_many_to_many_same(self):
        user = User.objects.create(username='foo')
        compare(user,
                expected=User(
                    username='foo', first_name='', last_name='',
                    is_superuser=False
                ),
                ignore_fields=['id', 'date_joined'])
