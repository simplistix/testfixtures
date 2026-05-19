import logging

import pytest

pytest.importorskip("structlog")

import structlog
from structlog.contextvars import bind_contextvars, bound_contextvars, clear_contextvars

from testfixtures import (
    LogCapture,
    ShouldNotWarn,
    ShouldRaise,
    ShouldWarn,
    compare,
)
from testfixtures.logcapture import LoggingSource
from testfixtures.mock import Mock
from testfixtures.structlog import StructlogSource, level_name, raw


@pytest.fixture(autouse=True)
def clean_structlog():
    structlog.reset_defaults()
    clear_contextvars()
    yield
    structlog.reset_defaults()
    clear_contextvars()


class TestLogCapture:
    def test_simple(self):
        with LogCapture(StructlogSource()) as log:
            structlog.get_logger().info('hello world')
        log.check(('INFO', 'hello world'))

    def test_fields_single(self):
        with LogCapture(StructlogSource(('event',))) as log:
            structlog.get_logger().info('just the event')
        log.check('just the event')

    def test_attributes_bare_string(self):
        with LogCapture(StructlogSource('event')) as log:
            structlog.get_logger().info('just the event')
        log.check('just the event')

    def test_fields_callable(self):
        logger = structlog.get_logger()
        with LogCapture(StructlogSource((lambda d: d['level'].upper(), 'event'))) as log:
            logger.debug('msg1')
            logger.info('msg2')
        log.check(
            ('DEBUG', 'msg1'),
            ('INFO', 'msg2'),
        )

    def test_attributes_single_callable(self):
        logger = structlog.get_logger()
        with LogCapture(StructlogSource(raw)) as log:
            logger.info('hello')
            logger.error('boom')
        log.check(
            {'level': 'info', 'event': 'hello'},
            {'level': 'error', 'event': 'boom'},
        )

    def test_exception(self):
        with LogCapture(StructlogSource()) as log:
            try:
                raise ValueError('boom')
            except ValueError:
                structlog.get_logger().exception('oh no')
        log.check(('ERROR', 'oh no'))
        log.check_exception_str('boom')
        with ShouldRaise(ValueError('boom')):
            log.raise_first_exception()
        compare(log.entries[0].exception, expected=ValueError('boom'))

    def test_level_filtering(self):
        with LogCapture(StructlogSource(level='WARNING')) as log:
            structlog.get_logger().info('ignored')
            structlog.get_logger().warning('captured')
        log.check(('WARNING', 'captured'))

    def test_broken_attribute_method(self):
        def bad(event_dict):
            raise ValueError('boom')

        with LogCapture(StructlogSource((bad,))) as log:
            with ShouldRaise(ValueError('boom')):
                structlog.get_logger().info('task logging')
        log.check()

    def test_bound_contextvars(self):
        with LogCapture(StructlogSource(raw)) as log:
            with bound_contextvars(task=1234):
                structlog.get_logger().info('task logging')
        log.check({'event': 'task logging', 'level': 'info', 'task': 1234})

    def test_bind_contextvars(self):
        bind_contextvars(request_id='abc123')
        logger = structlog.get_logger()
        with LogCapture(StructlogSource(raw)) as log:
            logger.info('handling')
            logger.info('done')
        log.check(
            {'event': 'handling', 'level': 'info', 'request_id': 'abc123'},
            {'event': 'done', 'level': 'info', 'request_id': 'abc123'},
        )

    def test_bind(self):
        logger = structlog.get_logger().bind(ip='192.168.0.1', user='someone')
        with LogCapture(StructlogSource((level_name, 'event', 'ip', 'user', 'other'))) as log:
            logger.info('Contextualize your logger easily')
            logger.bind(other='foo').info('Inline binding of extra attribute')
        log.check(
            ('INFO', 'Contextualize your logger easily', '192.168.0.1', 'someone', None),
            ('INFO', 'Inline binding of extra attribute', '192.168.0.1', 'someone', 'foo'),
        )

    def test_processor_chain_restored_after_capture(self):
        rendered: list[str] = []

        def render(logger, method_name, event_dict):
            rendered.append(text := f"{event_dict['level']}: {event_dict['event']}")
            return text

        structlog.configure(processors=[structlog.stdlib.add_log_level, render])

        logger = structlog.get_logger()
        logger.info('before capture')
        with LogCapture(StructlogSource()) as log:
            logger.info('during capture')
        logger.info('after capture')

        log.check(('INFO', 'during capture'))
        compare(rendered, expected=['info: before capture', 'info: after capture'])

    def test_renderer_in_processors(self):
        with LogCapture(
            StructlogSource(
                attributes=raw,
                processors=[
                    structlog.contextvars.merge_contextvars,
                    structlog.processors.KeyValueRenderer(sort_keys=True),
                ],
            )
        ) as log:
            structlog.get_logger().bind(user='alice').info('hi')
        log.check("event='hi' user='alice'")

    def test_processors_supplied_excluding_loglevel(self):
        logger = structlog.get_logger().bind(user='alice')
        with LogCapture(
            StructlogSource(
                attributes=raw,
                processors=[structlog.processors.KeyValueRenderer(sort_keys=True)],
                level='WARNING',
            ),
        ) as log:
            logger.info('hi from info')
            logger.warning('hi from warning')
        # note that filtering still works:
        log.check("event='hi from warning' user='alice'")

    def test_combined_logging(self):
        with LogCapture(StructlogSource(), LoggingSource()) as log:
            for level in 'info', 'warning':
                getattr(logging, level)('from stdlib')
                getattr(structlog.get_logger(), level)('from structlog')
        log.check(
            ('INFO', 'from stdlib'),
            ('INFO', 'from structlog'),
            ('WARNING', 'from stdlib'),
            ('WARNING', 'from structlog'),
        )

    def test_displaced_by_reset_defaults_warns(self):
        with ShouldWarn(
            UserWarning(
                'StructlogSource was displaced from structlog configuration before uninstall.\n'
                'Avoid calling structlog.configure() or structlog.reset_defaults() '
                'inside a LogCapture block.'
            )
        ):
            with LogCapture(StructlogSource()):
                structlog.reset_defaults()

    def test_displaced_by_reconfigure_warns(self):
        processors_before = structlog.get_config()['processors']
        with ShouldWarn(
            UserWarning(
                'StructlogSource was displaced from structlog configuration before uninstall.\n'
                'Avoid calling structlog.configure() or structlog.reset_defaults() '
                'inside a LogCapture block.'
            )
        ):
            with LogCapture(StructlogSource()) as cap:
                structlog.get_logger().info('captured before displacement')
                structlog.configure(processors=[structlog.processors.KeyValueRenderer()])
                # Anything logged after the user swapped the list reference goes
                # through their new chain, not our capture — nothing we can do
                # about that. We still warn and restore the original config on
                # uninstall.
                structlog.get_logger().bind(after='displacement').info('lost')
        cap.check(('INFO', 'captured before displacement'))
        compare(structlog.get_config()['processors'], expected=processors_before)

    def test_uninstall_does_not_warn(self):
        with ShouldNotWarn():
            with LogCapture(StructlogSource()):
                structlog.get_logger().info('hi')
