import pytest

pytest.importorskip("loguru")

from loguru import logger

from testfixtures import LogCapture, ShouldRaise
from testfixtures.loguru import LoguruSource


class TestLogCapture:

    def make_capture(self, **kw):
        capture = LogCapture(sources=[LoguruSource(**kw)], install=False)
        capture.install()
        return capture

    def test_simple(self):
        with self.make_capture() as log:
            logger.info('hello world')
            log.check(('INFO', 'hello world'))

    def test_fields_single(self):
        with self.make_capture(fields=(lambda r: r['message'],)) as log:
            logger.info('just the message')
            log.check('just the message')

    def test_fields_callable(self):
        with self.make_capture(fields=(lambda r: r['level'].name, lambda r: r['message'])) as log:
            logger.debug('msg1')
            logger.info('msg2')
            log.check(
                ('DEBUG', 'msg1'),
                ('INFO', 'msg2'),
            )

    def test_exception(self):
        with self.make_capture() as log:
            try:
                raise ValueError('boom')
            except ValueError:
                logger.exception('oh no')
            log.check(('ERROR', 'oh no'))
            log.check_exception_str('boom')

    def test_raise_first_exception(self):
        with self.make_capture() as log:
            try:
                raise ValueError('boom')
            except ValueError:
                logger.exception('oh no')
            with ShouldRaise(ValueError('boom')):
                log.raise_first_exception()

    def test_order_doesnt_matter(self):
        with self.make_capture() as log:
            logger.info('first')
            logger.info('second')
            log.check(
                ('INFO', 'second'),
                ('INFO', 'first'),
                order_matters=False,
            )

    def test_level_filtering(self):
        with self.make_capture(level='WARNING') as log:
            logger.info('ignored')
            logger.warning('captured')
            log.check(('WARNING', 'captured'))
