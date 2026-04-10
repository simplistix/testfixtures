import logging

import pytest

from testfixtures.logcapture import LoggingSource

pytest.importorskip("loguru")

from loguru import logger

from testfixtures import LogCapture, ShouldRaise
from testfixtures.loguru import LoguruSource

@pytest.fixture(autouse=True)
def clean_loguru():
    logger.remove()
    yield
    logger.remove()


class TestLogCapture:

    def test_simple(self):
        with LogCapture(LoguruSource()) as log:
            logger.info('hello world')
        log.check(('INFO', 'hello world'))

    def test_fields_single(self):
        with LogCapture(LoguruSource(('message', ))) as log:
            logger.info('just the message')
        log.check('just the message')

    def test_fields_callable(self):
        with LogCapture(LoguruSource((lambda r: r['level'].name, 'message'))) as log:
            logger.debug('msg1')
            logger.info('msg2')
        log.check(
            ('DEBUG', 'msg1'),
            ('INFO', 'msg2'),
        )

    def test_exception(self):
        with LogCapture(LoguruSource()) as log:
            try:
                raise ValueError('boom')
            except ValueError:
                logger.exception('oh no')
        log.check(('ERROR', 'oh no'))
        log.check_exception_str('boom')

    def test_raise_first_exception(self):
        with LogCapture(LoguruSource()) as log:
            try:
                raise ValueError('boom')
            except ValueError:
                logger.exception('oh no')
        with ShouldRaise(ValueError('boom')):
            log.raise_first_exception()

    def test_order_doesnt_matter(self):
        with LogCapture(LoguruSource()) as log:
            logger.info('first')
            logger.info('second')
        log.check(
            ('INFO', 'second'),
            ('INFO', 'first'),
            order_matters=False,
        )

    def test_level_filtering(self):
        with LogCapture(LoguruSource(level='WARNING')) as log:
            logger.info('ignored')
            logger.warning('captured')
        log.check(('WARNING', 'captured'))

    def test_str(self):
        with LogCapture(LoguruSource()) as log:
            logger.info('hello world')
        assert str(log) == "INFO hello world"

    def test_combined_logging(self):
        with LogCapture(LoguruSource(), LoggingSource()) as log:
            for level in 'info', 'warning':
                getattr(logging, level)('from stdlib')
                getattr(logger, level)('from loguru')
        log.check(
            ('INFO', 'from stdlib'),
            ('INFO', 'from loguru'),
            ('WARNING', 'from stdlib'),
            ('WARNING', 'from loguru'),
        )
