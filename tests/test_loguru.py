import logging
from pathlib import Path

import pytest

from testfixtures.logcapture import LoggingSource
from testfixtures.mock import Mock, call, _Call as Call
from testfixtures import (
    LogCapture,
    ShouldNotWarn,
    ShouldRaise,
    ShouldWarn,
    StringComparison,
    compare,
)

pytest.importorskip("loguru")

from loguru import logger
from testfixtures.loguru import LoguruSource, level_name


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

    def test_attributes_bare_string(self):
        with LogCapture(LoguruSource('message')) as log:
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

    def test_attributes_single_callable(self):
        def extract(record):
            return {'level': record['level'].name, 'message': record['message']}

        with LogCapture(LoguruSource(extract)) as log:
            logger.info('hello')
            logger.error('boom')
        log.check(
            {'level': 'INFO', 'message': 'hello'},
            {'level': 'ERROR', 'message': 'boom'},
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

    def test_broken_attribute_method(self) -> None:

        def raw(e):
            raise ValueError("boom")

        with LogCapture(LoguruSource((raw,))) as log:
            with ShouldRaise(ValueError("boom")):
                    logger.info("task logging")
        log.check()

    def test_contextualize(self) -> None:
        with LogCapture(LoguruSource((level_name, 'message', 'extra'))) as log:
            with logger.contextualize(task=1234):
                logger.info("task logging")
        log.check(('INFO', 'task logging', {'task': 1234}))

    def test_bind(self) -> None:
        with LogCapture(LoguruSource((level_name, 'message', 'extra'))) as log:
            context_logger = logger.bind(ip="192.168.0.1", user="someone")
            context_logger.info("Contextualize your logger easily")
            context_logger.bind(other="foo").info("Inline binding of extra attribute")
            context_logger.info("Use kwargs to add context during formatting: {user}", user="me")
        log.check(
            ('INFO',
             'Contextualize your logger easily',
             {'ip': '192.168.0.1', 'user': 'someone'}),
            ('INFO',
             'Inline binding of extra attribute',
             {'ip': '192.168.0.1', 'user': 'someone', 'other': 'foo'}),
            ('INFO',
             'Use kwargs to add context during formatting: me',
             {'ip': '192.168.0.1', 'user': 'me'})
        )

    def test_serialize(self):
        sink = Mock()
        logger.add(sink, serialize=True)
        logger.info('before capture')
        with LogCapture(LoguruSource()) as log:
            logger.info('during capture')
        logger.info('after capture')
        log.check(('INFO', 'during capture'))

        def write_call(message: str) -> Call:
            return call.write(
                StringComparison(
                    (
                        r'{"text": ".+ \| INFO +\| tests.test_loguru:test_serialize:\d+'
                        r' - MESSAGE\\n", "record": {"elapsed": {"repr": "0.+", "seconds": .+}, '
                        r'"exception": null, "extra": {}, '
                        r'"file": {"name": "test_loguru.py", "path": ".+"}, '
                        '"function": "test_serialize", '
                        r'"level": {"icon": "ℹ️", "name": "INFO", "no": 20}, "line": \d+, '
                        '"message": "MESSAGE", '
                        '"module": "test_loguru", "name": "tests.test_loguru", '
                        '"process": {.+}, '
                        '"thread": {.+}, '
                        '"time": {"repr": ".+", "timestamp": .+}}}\n'
                  ).replace('MESSAGE', message)
            ))

        compare(sink.mock_calls, expected=[
            write_call('before capture'),
            call.flush(),
            write_call('after capture'),
            call.flush(),
        ])

    def test_format(self, tmp_path: Path):
        log_file= tmp_path / "file.log"
        logger.add(log_file, format="{level} {extra[ip]} {extra[user]} {message}")
        with logger.contextualize(ip="192.168.0.1", user="someone"):
            logger.info('before capture')
            with LogCapture(LoguruSource()) as log:
                logger.info('during capture')
            logger.info('after capture')
        compare(
            log_file.read_text(),
            expected=(
                "INFO 192.168.0.1 someone before capture\n"
                "INFO 192.168.0.1 someone after capture\n"
            )
        )


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

    def test_shutdown_while_installed(self):
        with LogCapture(LoguruSource()):
            with ShouldWarn(UserWarning(
                'LoguruSource left installed at shutdown.\n'
                'Call uninstall() or use LogCapture as a context manager.'
            )):
                logger.remove()

    def test_uninstall_does_not_warn(self):
        with ShouldNotWarn():
            with LogCapture(LoguruSource()):
                logger.info('hi')
