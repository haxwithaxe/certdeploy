"""A helper utility that keeps pytest from throwing warnings.

A helper utility that keeps pytest from throwing warnings without generating
noise in pytest.
"""

import threading
import time
from typing import Any

import pytest


class CleanThread(threading.Thread):
    """A thread that handles exceptions and allows for graceful exits."""

    def __init__(
        self,
        func: callable,
        args: list[Any] = None,
        kwargs: dict[str, Any] = None,
        allowed_exceptions: list[Exception] = None,
        kill_switch: threading.Event = None,
        reraise: bool = False
    ):
        """Prepare a thread.

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
        if not allowed_exceptions:
            raise ValueError(
                'allowed_exceptions must have at least one exception'
            )
        threading.Thread.__init__(self, daemon=True)
        self.func = func
        self.args = args or []
        self.kwargs = kwargs or {}
        self.allowed_exceptions = allowed_exceptions or []
        self.kill_switch = kill_switch or threading.Event()
        self.expected_exception: Exception = None
        self.unexpected_exception: Exception = None
        self.reraise = reraise

    def run(self):
        """Run `self.func` when `self.start` is called.

        Don't call this directly.
        """
        try:
            self.func(*self.args, **self.kwargs)
        except self.allowed_exceptions as err:
            # Make expected exceptions available for inspection
            self.expected_exception = err
        except Exception as err:
            # Hold on to unexpected exceptions for reraising later
            self.unexpected_exception = err

    def stop(self, timeout: int = None):
        """Stop the code is `self.func` if `self.kill_switch` is attached.

        Also join the thread and raise any unexpected exception if
        `self.reraise` is `True`.
        """
        self.kill_switch.set()
        time.sleep(0.1)
        self.join(timeout=timeout)
        if self.reraise and self.unexpected_exception:
            raise self.unexpected_exception


@pytest.fixture()
def simple_thread():
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
        thread = CleanThread(func, args, kwargs, allowed_exceptions,
                             kill_switch, reraise)
        threads.append(thread)
        return thread

    yield _simple_thread
    for thread in threads:
        thread.stop()
