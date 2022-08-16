"""quickdemo.debug - Provides useful helpers for quick debugging."""

import io
import sys

from contextlib import contextmanager
from quickdemo import _args_string

_indent_width = 0
_indent_depth = 0
_active = False
_print_invocation = False
_print_result = False
_print_exception = False


class _Indenter(io.TextIOBase):
    def __init__(self, base):
        self.base = base
        self.new_line_starting = True

    def flush(self):
        return self.base.flush()

    def isatty(self):
        return self.base.isatty()

    def writable(self):
        return True

    def write(self, text):
        global _indent_depth, _indent_width
        indent = ' ' * _indent_depth * _indent_width
        if self.new_line_starting:
            self.base.write(indent)
            self.new_line_starting = False
        if text.endswith("\n"):
            padded = text[:-1].replace("\n", "\n" + indent) + "\n"
            self.new_line_starting = True
        else:
            padded = text.replace("\n", "\n" + indent)
        self.base.write(padded)


def trace(f):
    def wrapper(*args, **kwargs):
        global _indent_depth, _active, _print_invocation, _print_result
        if _active and _print_invocation:
            print(f"{f.__name__}({_args_string(args, kwargs)}) invoked", file=sys.stderr)
        if _active:
            _indent_depth += 1
        try:
            result = f(*args, **kwargs)
        except Exception as e:
            if _active and _print_exception:
                print(f"{f.__name__}({_args_string(args, kwargs)}) -> {type(e).__name__}", file=sys.stderr)
            if _active:
                _indent_depth = max(_indent_depth - 1, 0)
            raise
        if _active and _print_result:
            print(f"{f.__name__}({_args_string(args, kwargs)}) -> {result}", file=sys.stderr)
        if _active:
            _indent_depth = max(_indent_depth - 1, 0)
        return result
    return wrapper


@contextmanager
def activate_trace(
        initial_depth=0,
        indent_width=2,
        redirect_streams=True,
        print_invocation=True,
        print_result=True,
        print_exception=True):
    global _indent_depth, _indent_width, _active, _print_invocation, _print_result, _print_exception
    _active = True
    _indent_depth = initial_depth
    _indent_width = indent_width
    _print_invocation = print_invocation
    _print_result = print_result
    _print_exception = print_exception
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    if redirect_streams:
        sys.stdout = sys.stderr = _Indenter(old_stderr)
    yield
    _active = False
    sys.stdout = old_stdout
    sys.stderr = old_stderr
