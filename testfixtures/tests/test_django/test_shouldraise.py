from django.core.exceptions import ValidationError

from testfixtures import ShouldRaise, compare
from testfixtures.compat import PY2


class TestShouldRaiseWithValidatorErrors(object):

    def test_as_expected(self):
        with ShouldRaise(ValidationError("d'oh")):
            raise ValidationError("d'oh")

    def test_not_as_expected(self):
        if PY2:
            message = (
                'ValidationError([u"d\'oh"]) (expected) != '
                'ValidationError([u\'nuts\']) (actual)'
            )
        else:
            message = (
                'ValidationError(["d\'oh"]) (expected) != '
                'ValidationError([\'nuts\']) (actual)'
            )
        try:
            with ShouldRaise(ValidationError("d'oh")):
                raise ValidationError("nuts")
        except AssertionError as e:
            compare(str(e), expected=message)
        else:
            raise AssertionError('No exception raised!')
