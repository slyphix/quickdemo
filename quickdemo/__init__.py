"""quickdemo - Library for immediate code execution and validation"""
import copy
import pickle
import quickdemo.formatters as fmt

from collections import defaultdict, namedtuple

# ----------------------------------------------------------------------------
#   GLOBALS
# ----------------------------------------------------------------------------

_group_store = defaultdict(set)

_default_formatter = fmt.fancy_printer
_default_options = {}

_serialize_protocol_version = 1
# reserved for future use
_serialize_options = namedtuple('_serialize_options', [], defaults=[])

# ----------------------------------------------------------------------------
#   OPERATIONS
# ----------------------------------------------------------------------------

class DemoStateError(Exception):
    def __init__(self, message):
        super().__init__(message)


def run(*args, **kwargs):
    """Run the decorated function with the specified arguments."""
    def wrapper(f):
        demo.with_function(f).with_args(*args, **kwargs).run()
        return f
    return wrapper


def apply(config):
    """Run the decorated function with the specified configuration."""
    def wrapper(f):
        config.with_function(f).run()
        return f
    return wrapper


def group(*group_ids):
    """Add the decorated function to the specified group."""
    def wrapper(f):
        global _group_store
        for gid in group_ids:
            _group_store[gid].add(f)
        return f
    return wrapper


def reset_groups():
    """Reset the global group store."""
    global _group_store
    _group_store.clear()


class arguments:
    """Stores arguments and keyword arguments used for function invocation."""
    __slots__ = 'args', 'kwargs'

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (self.args, self.kwargs) == (other.args, other.kwargs)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return f'arguments({formatters.args_string(self.args, self.kwargs)})'

    def __str__(self):
        return repr(self)


run_result = namedtuple('run_result', ['function', 'arguments', 'return_value'])


class _demo:
    __slots__ = '_functions', '_groups', '_arguments', '_options', '_formatter'

    def __init__(self):
        self._functions = []
        self._groups = set()
        self._arguments = []
        self._options = _default_options
        self._formatter = _default_formatter

    def with_function(self, *funcs):
        """Add the specified function to the run configuration."""
        modified = copy.deepcopy(self)
        modified._functions += funcs
        return modified

    def with_group(self, *groups):
        """Add the specified group to the run configuration."""
        modified = copy.deepcopy(self)
        modified._groups |= set(groups)
        return modified

    def with_args(self, *args, **kwargs):
        """Add the specified argument configuration to the run configuration."""
        modified = copy.deepcopy(self)
        if len(args) > 0 and all(isinstance(arg, arguments) for arg in args):
            modified._arguments.extend(args)
        else:
            modified._arguments.append(arguments(*args, **kwargs))
        return modified

    def with_args_iter(self, iterable):
        """Add the specified arguments to the run configuration.

        Intended for use with generator expressions."""
        all_args = []

        for element in iterable:
            if not isinstance(element, arguments):
                raise DemoStateError("with_args_iter only accepts objects of type argument")
            all_args.append(element)

        modified = copy.deepcopy(self)
        modified._arguments.extend(all_args)
        return modified

    def with_formatter(self, formatter):
        """Use the specified formatter for this run configuration."""
        modified = copy.deepcopy(self)
        modified._formatter = formatter
        return modified

    def with_options(self, **options):
        """Add the specified options to the run configuration."""
        modified = copy.deepcopy(self)
        modified._options.update(options)
        return modified

    def _slots(self):
        return (slot for slot in self.__slots__ if hasattr(self, slot))

    def __copy__(self):
        clone = type(self)()
        for slot in self._slots():
            setattr(clone, slot, getattr(self, slot))
        return clone

    def __deepcopy__(self, memo=None):
        if not memo:
            memo = {}
        clone = type(self)()
        for slot in self._slots():
            setattr(clone, slot, copy.deepcopy(getattr(self, slot), memo))
        return clone

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return (
            f"<demo object with {len(self._functions)} functions | "
            f"groups={self._groups}, arguments={self._arguments}, "
            f"options={self._options}, formatter={self._formatter}>"
        )

    def __eq__(self, other):
        return NotImplemented

    def __ne__(self, other):
        return NotImplemented

    def _resolve_groups(self):
        global _group_store
        return [f for g in self._groups for f in _group_store[g]]

    def _fetch_functions(self):
        return self._functions + self._resolve_groups()

    def _get_option(self, key, *, default):
        return self._options.get(key, default)

    def run(self):
        """Execute this run configuration."""
        all_functions = self._fetch_functions()
        if not all_functions:
            raise DemoStateError("No functions to run.")

        all_arguments = self._arguments if self._arguments else [arguments()]

        for func in all_functions:
            for ar in all_arguments:
                result = func(*ar.args, **ar.kwargs)
                if result is not None or self._get_option('print_none', default=False):
                    self._formatter(run_result(func, ar, result))

    def store(self, file):
        """Stores this run configuration in the specified file."""
        def write(output):
            # dump meta information
            pickle.dump((_serialize_protocol_version, options), output)
            # dump class state
            pickle.dump((self._arguments, self._options, self._formatter), output)

        options = _serialize_options()
        if isinstance(file, str):
            with open(file, 'wb') as actual_file:
                write(actual_file)
        else:
            write(file)


demo = _demo()


def load(file):
    """Deserializes the run configuration from the specified file."""
    def read_file(input_file):
        output = _demo()
        # load meta information
        pv, options = pickle.load(input_file)
        if pv != _serialize_protocol_version:
            raise Warning(f"'{file}' uses a different serialization protocol version."
                          f"Importing may produce unexpected results.")
        # load class state
        output._arguments, output._options, output._formatter = pickle.load(input_file)
        return output

    if isinstance(file, str):
        with open(file, 'rb') as actual_file:
            return read_file(actual_file)
    return read_file(file)
