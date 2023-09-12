"""A helper utility that keeps pytest from throwing warnings.

A helper utility that keeps pytest from throwing warnings without generating
noise in pytest.
"""

import threading
import time
from typing import Any, Callable

import pytest
from fixtures.utils import KillSwitch


class _WontBeThrownException(Exception):
    """An exception that won't match anything raised elsewhere."""


class CleanThread(threading.Thread):
    """A thread that handles exceptions and allows for graceful exits.

    Attributes:
        return_value: The return value of `func`.
        expected_exception: The expected exception if it has been caught. Just
            incase it's needed for inspection.
        unexpected_exception: Any unexpected exception that was raised by
            `func`.

    Arguments:
        func: A `callable` that takes `*args` as arguments and `**kwargs` as
            keyword arguments.
        args: A `list` of positional arguments. Defaults to an empty `list`.
        kwargs: A `dict` of keyword arguments. Defaults to an empty `dict`.
        allowed_exceptions: A `list` of allowable exceptions. Defaults to a
            `list` with an exception that won't be thrown by anything. The
            effect being nothing will be caught.
        kill_switch: A `threading.Event` that will stop the code when set.
            Defaults to a fresh `threading.Event`.
        reraise: If `True` any unexpected exception is reraised when the
            thread is stopped. Defaults to `False`.
        caplog: A `caplog` fixture to capture more output.

    Example:
        This is an example of how to use this class directly, not an
        example of how to use this in a test.

        ```
        my_kill_switch = threading.Event()

        def some_loop():
            while not my_kill_switch.is_set():
                do_something_dangerous()  # Raises `DangerZone` sometimes
                time.sleep(0.1)

        thread = CleanThread(
            some_loop,
            allowed_exceptions=[DangerZone],
            kill_switch=my_kill_switch
        )
        thread.start()
        # Sometimes this causes `do_something_dangerous` to raise
        #   `DangerZone` after `some_loop` has served it's purpose.
        do_something_interesting()
        thread.stop()
        ```
    """

    def __init__(  # noqa: D107
        self,
        func: callable,
        args: list[Any] = None,
        kwargs: dict[str, Any] = None,
        allowed_exceptions: list[Exception] = None,
        kill_switch: KillSwitch = None,
        teardown: Callable[[], None] = None,
        reraise: bool = False,
        caplog: pytest.LogCaptureFixture = None
    ):
        threading.Thread.__init__(self, daemon=True)
        self.func = func
        self.args = args or []
        self.kwargs = kwargs or {}
        # _WontBeThrownException is just an exception that won't be raised by
        #   anything the `except` statement doesn't like empty lists as
        #   parameters. Also the default shouldn't be to catch everything.
        self.allowed_exceptions = (_WontBeThrownException,)
        if allowed_exceptions:
            self.allowed_exceptions = allowed_exceptions
        self.kill_switch = kill_switch
        if self.kill_switch is None:
            self.kill_switch = KillSwitch()
        self.teardown = teardown or (lambda: None)
        self.reraise = reraise
        self.caplog = caplog
        self.return_value: Any = None
        # Just in case the expected error needs to be inspected
        self.expected_exception: Exception = None
        self.unexpected_exception: Exception = None

    def reraise_unexpected(self):
        """Reraise any unexpected exception."""
        if self.unexpected_exception:
            raise self.unexpected_exception

    def run(self):
        """Run `self.func` when `self.start` is called.

        Don't call this directly.
        """
        try:
            self.return_value = self.func(*self.args, **self.kwargs)
        except self.allowed_exceptions as err:
            # Make expected exceptions available for inspection
            self.expected_exception = err
        except Exception as err:
            # Hold on to unexpected exceptions for reraising later
            self.unexpected_exception = err

    def wait_for_condition(self, condition: Callable[['CleanThread'], bool],
                           timeout: int = 60) -> bool:
        """Wait for some `condition` in the thread to be `True`.

        When the thread dies the wait is terminated as if the `condition` has
        returned `True`.

        Arguments:
            condition: A function that takes this instance of this class as an
                argument and returns a `bool`.
            timeout: The number of seconds to wait for the thread to finish.
                Defaults to `60`.

        Returns:
            `True` if the condition was met.
            `False` if the thread is dead.

        Raises:
            TimeoutError: When `timeout` seconds have passed and `conditions`
                are still not met.
        """
        print(timeout)
        countdown = int(timeout / 0.1)
        for tick in range(countdown):
            print(tick)
            if not self.is_alive():
                print('thread died')
                return False
            print('running condition')
            if condition(self):
                print('condition met')
                return True
            time.sleep(0.1)
        raise TimeoutError()

    def wait_for_text_in_log(self, text: str,
                             log_selector: Callable[['CleanThread'], str],
                             timeout: int = 60):
        """Wait for some `text` to appear in the output of `log_selector`.

        As long as `text` and `log_selector` are usable with an `in` statement
        they don't have to be/return strings.

        Arguments:
            text: The string to look for in the logs.
            log_selector: A function that takes this instance of this class as
                an argument and returns the logs.
            timeout: The number of seconds to wait for the thread to finish.
                Defaults to `60`.

        Returns:
            `True` if the condition was met.
            `False` if the thread is dead.

        Raises:
            TimeoutError: When `timeout` seconds have passed and `text` has not
                been found in the logs.
        """
        print('wait for text in log')
        return self.wait_for_condition(
            lambda x: text in log_selector(x),
            timeout
        )

    def stop(self, timeout: int = None, reraise: bool = None):
        """Stop the code is `self.func` if `self.kill_switch` is attached.

        Also join the thread and raise any unexpected exception if
        `self.reraise` is `True`.
        """
        print('Set kill switch')
        self.kill_switch.set()
        print('Kill switch status', self.kill_switch.id, bool(self.kill_switch))
        time.sleep(0.1)
        print('Join thread')
        self.join(timeout=timeout)
        print('Teardown')
        self.teardown()
        if reraise is False:
            return
        if True in (reraise, self.reraise) and self.unexpected_exception:
            raise self.unexpected_exception

    def __repr__(self):
        """Return a pragmatic representation of this instance."""
        return (
            '<{self.__class__.__name__} '
            f'func={self.func}, '
            f'args={self.args}, '
            f'kwargs={self.kwargs}, '
            f'allowed_exceptions={self.allowed_exceptions}, '
            f'kill_switch={self.kill_switch.is_set()}, '
            f'return_value={self.return_value}, '
            f'expected_exception={self.expected_exception}, '
            f'unexpected_exception={self.unexpected_exception}, '
            f'reraise={self.reraise}, '
            f'caplog={self.caplog}, '
            f'is_alive={self.is_alive()}, '
            '>'
        )


@pytest.fixture(scope='function')
def simple_thread(caplog):
    """Return a factory for threads that will handle exceptions.

    Example:
        This is an example of how to use this class directly, not an
        example of how to use this in a test.

        ```
        class SomeTestHelper:

            my_kill_switch = threading.Event()

            def some_loop(self):
                while not self.my_kill_switch.is_set():
                    do_something_dangerous()  # Raises `DangerZone` sometimes
                    time.sleep(0.1)

        def test_something_interesting(simple_thread: callable):
            helper = SomeTestHelper()
            thread = simple_thread(
                helper.some_loop,
                allowed_exceptions=[DangerZone],
                kill_switch=helper.my_kill_switch
            )
            thread.start()
            # Sometimes this causes `do_something_dangerous` to raise
            #   `DangerZone` after `some_loop` has served it's purpose.
            do_something_interesting()
            thread.stop()
        ```

    """
    threads = []

    def _simple_thread(
        func: callable,
        args: list[Any] = None,
        kwargs: dict[str, Any] = None,
        allowed_exceptions: list[Exception] = None,
        kill_switch: threading.Event = None,
        teardown: Callable[[], None] = None,
        reraise: bool = True
    ):
        """Return a thread that handles errors.

        Arguments:
            func: A `callable` that takes `*args` as arguments and `**kwargs` as
                keyword arguments.
            args: A `list` of positional arguments. Defaults to an empty `list`.
            kwargs: A `dict` of keyword arguments. Defaults to an empty `dict`.
            allowed_exceptions: A `list` of allowable exceptions. Defaults to an
                empty `list`.
            kill_switch: A `threading.Event` that will stop the code when set.
                Defaults to a fresh `threading.Event`.
            reraise: If `True` any unexpected exception is reraised when the
                thread is stopped. Defaults to `False`.
        """
        thread = CleanThread(
            func=func,
            args=args,
            kwargs=kwargs,
            allowed_exceptions=allowed_exceptions,
            kill_switch=kill_switch,
            teardown=teardown,
            reraise=reraise,
            caplog=caplog
        )
        threads.append(thread)
        return thread

    yield _simple_thread
    for thread in threads:
        thread.stop(reraise=False)


@pytest.fixture(scope='function')
def managed_thread(caplog):
    """Return a factory for started threads that will handle exceptions.

    Example:
        This is an example of how to use this class directly, not an
        example of how to use this in a test.

        ```
        class SomeTestHelper:

            my_kill_switch = threading.Event()

            def some_loop(self):
                while not self.my_kill_switch.is_set():
                    do_something_dangerous()  # Raises `DangerZone` sometimes
                    time.sleep(0.1)

        def test_something_interesting(managed_thread: callable):
            helper = SomeTestHelper()
            thread = managed_thread(
                helper.some_loop,
                allowed_exceptions=[DangerZone],
                kill_switch=helper.my_kill_switch
            )
            # Automatically started
            # Sometimes this causes `do_something_dangerous` to raise
            #   `DangerZone` after `some_loop` has served it's purpose.
            do_something_interesting()
            # Automatically stopped
        ```

    """
    threads = []

    def _managed_thread(
        func: callable,
        args: list[Any] = None,
        kwargs: dict[str, Any] = None,
        allowed_exceptions: list[Exception] = None,
        kill_switch: threading.Event = None,
        teardown: Callable[[], None] = None,
        reraise: bool = True
    ):
        """Return a thread that handles errors.

        Arguments:
            func: A `callable` that takes `*args` as arguments and `**kwargs` as
                keyword arguments.
            args: A `list` of positional arguments. Defaults to an empty `list`.
            kwargs: A `dict` of keyword arguments. Defaults to an empty `dict`.
            allowed_exceptions: A `list` of allowable exceptions. Defaults to an
                empty `list`.
            kill_switch: A `threading.Event` that will stop the code when set.
                Defaults to a fresh `threading.Event`.
            reraise: If `True` any unexpected exception is reraised when the
                thread is stopped. Defaults to `False`.
        """
        thread = CleanThread(
            func=func,
            args=args,
            kwargs=kwargs,
            allowed_exceptions=allowed_exceptions,
            kill_switch=kill_switch,
            teardown=teardown,
            reraise=reraise,
            caplog=caplog
        )
        threads.append(thread)
        thread.start()
        return thread

    yield _managed_thread
    for thread in threads:
        thread.stop(reraise=False)
