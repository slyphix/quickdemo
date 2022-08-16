"""quickdemo - Library for immediate code execution and validation"""

import copy
import itertools
import os
import pickle
import sys

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class _Anything:
    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False

    def __repr__(self):
        return "<anything>"

    def __str__(self):
        return "anything"


@dataclass(frozen=True)
class _Lazy:
    expression: str

    def __repr__(self):
        return f"Lazy({self.expression!r})"


# ----------------------------------------------------------------------------
#   GLOBALS
# ----------------------------------------------------------------------------


MINIMAL_OUTPUT_FORMAT = "{result}"
SIMPLE_OUTPUT_FORMAT = "{name}({fullargs}) -> {result}"
VERBOSE_OUTPUT_FORMAT = "{name} with arguments ({fullargs}) produced result {result}"
MINIMAL_ERROR_FORMAT = "{errorname}"
SIMPLE_ERROR_FORMAT = "{name}({fullargs}) -> {errorname}"
VERBOSE_ERROR_FORMAT = "{name} with arguments ({fullargs}) failed with {errorname}: {errormessage}"

TEST_OUTPUT_RESULT = "Passed: {name}({fullargs}) = {result}"
TEST_OUTPUT_NO_RESULT = "Passed: {name}({fullargs})"
TEST_ERROR_RESULT = "Passed: {name}({fullargs}) raised {errorname}"
TEST_ERROR_NO_RESULT = "Passed: {name}({fullargs})"

ANY = _Anything()


# ----------------------------------------------------------------------------
#   INTERNALS
# ----------------------------------------------------------------------------


_passed_test_count = 0
_failed_test_count = 0

_TRUTHY_VALUES = ["y", "yes", "on", "1"]
_disable = os.environ.get("QUICKDEMO_DISABLE", "").lower() in _TRUTHY_VALUES
_disable_output = os.environ.get("QUICKDEMO_DISABLE_OUTPUT", "").lower() in _TRUTHY_VALUES
_exit_on_test_failure = os.environ.get("QUICKDEMO_EXIT_ON_TEST_FAILURE", "").lower() in _TRUTHY_VALUES

_DEFAULT_OPTIONS = {
    "output_none": False,
    "output_format": SIMPLE_OUTPUT_FORMAT,
    "error_format": SIMPLE_ERROR_FORMAT,
    "expected_result_format": TEST_OUTPUT_NO_RESULT,
    "expected_error_format": TEST_ERROR_NO_RESULT,
    "wrong_result_format": "Failed: {name}({fullargs}) = {result}, expected {expected}",
    "wrong_error_format": "Failed: {name}({fullargs}) raised {errorname}, expected {expected}",
    "unexpected_result_format": "Failed: {name}({fullargs}) should raise {expected}, but no error was raised",
    "unexpected_error_format": "Failed: {name}({fullargs}) raised {errorname}, expected {expected}",
}

_SERIALIZE_PROTOCOL_VERSION = 2


def _args_string(args, kwargs, sep=", "):
    args_iter = (str(a) for a in args)
    kwargs_iter = (f'{k}={v}' for k, v in kwargs.items())
    return sep.join(itertools.chain(args_iter, kwargs_iter))


def _format(format_string, function, arguments, *, result: Union[object, Exception] = "", expected: object = ""):
    global _disable_output
    format_options = {
        "name": function.__name__,
        "args": _args_string(arguments.args, {}),
        "kwargs": _args_string((), arguments.kwargs),
        "fullargs": _args_string(arguments.args, arguments.kwargs),
        "result": result,
        "expected": expected.__name__ if isinstance(expected, type) else expected,
        "errorname": type(result).__name__ if isinstance(result, Exception) else "",
        "errormessage": str(result) if isinstance(result, Exception) else "",
    }
    if not _disable_output:
        print(format_string.format(**format_options), file=sys.stderr)


def _test_failed():
    global _exit_on_test_failure, _failed_test_count
    _failed_test_count += 1
    if _exit_on_test_failure:
        sys.exit(1)


def _test_passed():
    global _passed_test_count
    _passed_test_count += 1


# ----------------------------------------------------------------------------
#   OPERATIONS
# ----------------------------------------------------------------------------


def disable(state):
    global _disable
    _disable = state


def disable_output(state):
    global _disable_output
    _disable_output = state


def exit_on_test_failure(state):
    global _exit_on_test_failure
    _exit_on_test_failure = state


def reset_test_summary():
    global _passed_test_count, _failed_test_count
    _passed_test_count = _failed_test_count = 0


def print_test_summary():
    global _passed_test_count, _failed_test_count, _disable_output
    if not _disable_output:
        print(f"{_passed_test_count} tests passed, {_failed_test_count} tests failed.", file=sys.stderr)


def lazy(expression):
    return _Lazy(expression)


def run(*args, **kwargs):
    """Run the decorated function with the specified arguments."""
    return from_action(Run(Arguments(*args, **kwargs)))


def expect(expected_result, *args, **kwargs):
    """Run the decorated function with the specified arguments, expecting a fixed value."""
    return from_action(Expect(expected_result, Arguments(*args, **kwargs)))


def expect_any(*args, **kwargs):
    """Run the decorated function with the specified arguments, expecting no exception."""
    return from_action(Expect(ANY, Arguments(*args, **kwargs)))


def expect_error(expected_type, *args, **kwargs):
    """Run the decorated function with the specified arguments, expecting an exception."""
    return from_action(ExpectError(expected_type, Arguments(*args, **kwargs)))


def from_action(action):
    """Run the decorated function with the specified configuration."""
    def wrapper(f):
        builder().with_actions(action).build().run_on(f)
        return f
    return wrapper


def from_config(config):
    """Run the decorated function with the specified configuration."""
    def wrapper(f):
        config.run_on(f)
        return f
    return wrapper


def from_file(file):
    """Run the decorated function with the configuration from the specified file."""
    def wrapper(f):
        load(file).run_on(f)
        return f
    return wrapper


def builder():
    """Return a new builder."""
    return _DemoBuilder()


def load(file):
    """Deserialize the run configuration from the specified file."""
    if isinstance(file, str):
        with open(file, 'rb') as actual_file:
            return pickle.load(actual_file)
    return pickle.load(file)


class Arguments:
    """Stores arguments and keyword arguments used for function invocation."""
    __slots__ = '_args', '_kwargs', '_evaluated'

    @property
    def args(self):
        return self.evaluate()._args

    @property
    def kwargs(self):
        return self.evaluate()._kwargs

    def evaluate(self):
        if not self._evaluated:
            self._evaluated = True
            self._args = [
                eval(arg.expression, globals()) if isinstance(arg, _Lazy) else arg
                for arg in self._args
            ]
            self._kwargs = {
                key: eval(arg.expression, globals()) if isinstance(arg, _Lazy) else arg
                for key, arg in self._kwargs
            }
        return self

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and not kwargs and isinstance(args[0], Arguments):
            self._args = args[0]._args
            self._kwargs = args[0]._kwargs
            self._evaluated = args[0]._evaluated
        else:
            self._args = args
            self._kwargs = kwargs
            self._evaluated = False

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (self.args, self.kwargs) == (other.args, other.kwargs)

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return f"Arguments({_args_string(self._args, self._kwargs)})"

    def __str__(self):
        return repr(self)


class Action(ABC):
    def run(self, function, options):
        global _disable
        if not _disable:
            self.do_run(function, options)

    @abstractmethod
    def do_run(self, function, options):
        pass


@dataclass
class Run(Action):
    arguments: Arguments

    def do_run(self, function, options):
        try:
            result = function(*self.arguments.args, **self.arguments.kwargs)
            if result is not None or options["output_none"]:
                _format(options["output_format"], function, self.arguments, result=result)
        except Exception as error:
            _format(options["error_format"], function, self.arguments, result=error)


@dataclass
class Expect(Action):
    expected: object
    arguments: Arguments

    def __init__(self, expected, arguments):
        self.expected = expected
        self.arguments = arguments

    def do_run(self, function, options):
        try:
            result = function(*self.arguments.args, **self.arguments.kwargs)
            if result == self.expected:
                _format(options["expected_result_format"], function, self.arguments, result=result, expected=self.expected)
                _test_passed()
            else:
                _format(options["wrong_result_format"], function, self.arguments, result=result, expected=self.expected)
                _test_failed()
        except Exception as error:
            _format(options["unexpected_error_format"], function, self.arguments, result=error, expected=self.expected)
            _test_failed()


@dataclass
class ExpectError(Action):
    expected: type
    arguments: Arguments

    def __init__(self, expected, arguments):
        if not issubclass(expected, Exception):
            raise ValueError("the exception to expect does not inherit from Exception")
        self.expected = expected
        self.arguments = arguments

    def do_run(self, function, options):
        try:
            result = function(*self.arguments.args, **self.arguments.kwargs)
            _format(options["unexpected_result_format"], function, self.arguments, result=result, expected=self.expected)
            _test_failed()
        except Exception as error:
            if isinstance(error, self.expected):
                _format(options["expected_error_format"], function, self.arguments, result=error, expected=self.expected)
                _test_passed()
            else:
                _format(options["wrong_error_format"], function, self.arguments, result=error, expected=self.expected)
                _test_failed()


# ----------------------------------------------------------------------------
#   INTERNALS
# ----------------------------------------------------------------------------


class _DemoBase:
    __slots__ = '_actions', '_options'

    def __init__(self, *, actions, options):
        self._actions = actions
        self._options = options

    @classmethod
    def _copy_of(cls, inst):
        """Copy all attributes of this instance to a newly created instance."""
        new_inst = cls.__new__(cls)
        for slot in cls.__slots__:
            setattr(new_inst, slot, copy.deepcopy(getattr(inst, slot)))
        return new_inst

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} object with actions={self._actions}"
            f" and options={self._options}>"
        )

    def __eq__(self, other):
        return NotImplemented

    def __ne__(self, other):
        return NotImplemented


class _DemoBuilder(_DemoBase):

    def __init__(self):
        super().__init__(
            actions=[],
            options=_DEFAULT_OPTIONS.copy())

    def build(self):
        """Create a demo object using the current configuration."""
        return _Demo._copy_of(self)

    def with_actions(self, *actions):
        """Add the specified actions to the run configuration."""
        return self.with_actions_iter(actions)

    def with_actions_iter(self, iterable):
        """Add the specified actions to the run configuration.

        Intended for use with generator expressions."""
        for element in iterable:
            if not isinstance(element, Action):
                raise ValueError("with_actions only accepts actions")
            self._actions.append(element)
        return self

    def with_option(self, name, value):
        """Add the specified option to the run configuration."""
        self._options[name] = value
        return self

    def with_options(self, **options):
        """Add the specified options to the run configuration."""
        self._options.update(options)
        return self

    def __getstate__(self):
        return (
            _SERIALIZE_PROTOCOL_VERSION,
            (self._actions, self._options)
        )

    def __setstate__(self, state):
        self.__init__()
        version, data = state
        if version != _SERIALIZE_PROTOCOL_VERSION:
            raise Warning("Different serialization protocol version detected. "
                          "Importing may produce unexpected results.")
        self._actions, self._options = data


class _Demo(_DemoBase):
    def builder(self):
        """Create a mutable builder from the current object state."""
        return _DemoBuilder._copy_of(self)

    def run_on(self, function):
        for action in self._actions:
            action.run(function, self._options)
        return self

    def store(self, file):
        """Store this run configuration in the specified file."""
        if isinstance(file, str):
            with open(file, 'wb') as actual_file:
                pickle.dump(self, actual_file)
        else:
            pickle.dump(self, file)
        return self
