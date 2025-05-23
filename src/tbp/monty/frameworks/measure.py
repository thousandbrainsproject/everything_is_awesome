# Copyright 2025 Thousand Brains Project
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
"""Context manager for timing code execution."""

from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from functools import wraps
from time import perf_counter
from typing import Callable, Generator


@contextmanager
def timed_context() -> Generator[Callable[[], float], None, None]:
    """Context manager to measure elapsed time.

    Yields:
        Callable[[], float]: A function that returns the elapsed time in seconds.
    """
    t1 = t2 = perf_counter()
    yield lambda: t2 - t1
    t2 = perf_counter()


def measure_time(logger_name: str) -> Callable:
    """Decorator to measure the execution time of a function.

    Args:
        logger_name (str): The name of the logger to use for logging the execution time.

    Returns:
        Callable: A decorator that wraps the function to measure its execution time.
    """

    def decorator(func: Callable) -> Callable:
        """The actual decorator that wraps the function.

        Args:
            func (Callable): The function to wrap.

        Returns:
            Callable: The wrapped function with execution time measurement.
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            with timed_context() as timer:
                result = func(*args, **kwargs)

            logger = logging.getLogger(logger_name)
            if not logger.isEnabledFor(logging.DEBUG):
                return result

            operation = "method" if "." in func.__qualname__ else "function"
            event_args = {
                "event": "__call__",
                operation: func.__qualname__,
                "duration": timer(),
                "unit": "s",
            }
            logger.debug(json.dumps(event_args))
            return result

        return wrapper

    return decorator
