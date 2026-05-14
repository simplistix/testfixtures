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
from testfixtures.structlog import StructlogSource, level_name


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
        with LogCapture(StructlogSource((lambda d: d['level'].upper(), 'event'))) as log:
            structlog.get_logger().debug('msg1')
            structlog.get_logger().info('msg2')
        log.check(
            ('DEBUG', 'msg1'),
            ('INFO', 'msg2'),
        )

    def test_attributes_single_callable(self):
        def extract(event_dict):
            return {'level': event_dict['level'].upper(), 'event': event_dict['event']}

        with LogCapture(StructlogSource(extract)) as log:
            structlog.get_logger().info('hello')
            structlog.get_logger().error('boom')
        log.check(
            {'level': 'INFO', 'event': 'hello'},
            {'level': 'ERROR', 'event': 'boom'},
        )

    def test_exception(self):
        with LogCapture(StructlogSource()) as log:
            try:
                raise ValueError('boom')
            except ValueError:
                structlog.get_logger().exception('oh no')
        log.check(('ERROR', 'oh no'))
        log.check_exception_str('boom')

    def test_raise_first_exception(self):
        with LogCapture(StructlogSource()) as log:
            try:
                raise ValueError('boom')
            except ValueError:
                structlog.get_logger().exception('oh no')
        with ShouldRaise(ValueError('boom')):
            log.raise_first_exception()

    def test_order_doesnt_matter(self):
        with LogCapture(StructlogSource()) as log:
            structlog.get_logger().info('first')
            structlog.get_logger().info('second')
        log.check(
            ('INFO', 'second'),
            ('INFO', 'first'),
            order_matters=False,
        )

    def test_level_filtering(self):
        with LogCapture(StructlogSource(level='WARNING')) as log:
            structlog.get_logger().info('ignored')
            structlog.get_logger().warning('captured')
        log.check(('WARNING', 'captured'))

    def test_str(self):
        with LogCapture(StructlogSource()) as log:
            structlog.get_logger().info('hello world')
        compare(str(log), expected='INFO hello world')

    def test_broken_attribute_method(self):

        def raw(event_dict):
            raise ValueError('boom')

        with LogCapture(StructlogSource((raw,))) as log:
            with ShouldRaise(ValueError('boom')):
                structlog.get_logger().info('task logging')
        log.check()

    def test_bound_contextvars(self):
        with LogCapture(StructlogSource((level_name, 'event', 'task'))) as log:
            with bound_contextvars(task=1234):
                structlog.get_logger().info('task logging')
        log.check(('INFO', 'task logging', 1234))

    def test_bind_contextvars(self):
        bind_contextvars(request_id='abc123')
        with LogCapture(StructlogSource((level_name, 'event', 'request_id'))) as log:
            structlog.get_logger().info('handling')
            structlog.get_logger().info('done')
        log.check(
            ('INFO', 'handling', 'abc123'),
            ('INFO', 'done', 'abc123'),
        )

    def test_bind(self):
        with LogCapture(StructlogSource((level_name, 'event', 'ip', 'user'))) as log:
            context_logger = structlog.get_logger().bind(ip='192.168.0.1', user='someone')
            context_logger.info('Contextualize your logger easily')
            context_logger.bind(other='foo').info('Inline binding of extra attribute')
        log.check(
            ('INFO', 'Contextualize your logger easily', '192.168.0.1', 'someone'),
            ('INFO', 'Inline binding of extra attribute', '192.168.0.1', 'someone'),
        )

    def test_processor_chain_restored_after_capture(self):
        rendered: list[str] = []

        def render(logger, method_name, event_dict):
            rendered.append(f"{event_dict['level']}: {event_dict['event']}")
            return rendered[-1]

        structlog.configure(processors=[structlog.stdlib.add_log_level, render])

        structlog.get_logger().info('before capture')
        with LogCapture(StructlogSource()) as log:
            structlog.get_logger().info('during capture')
        structlog.get_logger().info('after capture')

        log.check(('INFO', 'during capture'))
        compare(rendered, expected=['info: before capture', 'info: after capture'])

    def test_renderer_in_processors(self):
        with LogCapture(
            StructlogSource(
                attributes='event',
                processors=[
                    structlog.contextvars.merge_contextvars,
                    structlog.processors.KeyValueRenderer(sort_keys=True),
                ],
            )
        ) as log:
            structlog.get_logger().bind(user='alice').info('hi')
        compare(
            log.entries[0].actual,
            expected="event='hi' level='info' user='alice'",
        )

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
        with ShouldWarn(UserWarning(
            'StructlogSource was displaced from structlog configuration before uninstall.\n'
            'Avoid calling structlog.configure() or structlog.reset_defaults() '
            'inside a LogCapture block.'
        )):
            with LogCapture(StructlogSource()):
                structlog.reset_defaults()

    def test_displaced_by_reconfigure_warns(self):
        processors_before = structlog.get_config()['processors']
        with ShouldWarn(UserWarning(
            'StructlogSource was displaced from structlog configuration before uninstall.\n'
            'Avoid calling structlog.configure() or structlog.reset_defaults() '
            'inside a LogCapture block.'
        )):
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
