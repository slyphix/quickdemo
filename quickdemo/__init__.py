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

# ----------------------------------------------------------------------------
#   OPERATIONS
# ----------------------------------------------------------------------------


class DemoStateError(Exception):
    def __init__(self, message):
        super().__init__(message)


def run(*args, **kwargs):
    """Run the decorated function with the specified arguments."""
    def wrapper(f):
        builder().with_function(f).with_args(*args, **kwargs).build().run()
        return f
    return wrapper


def apply(config):
    """Run the decorated function with the specified configuration."""
    def wrapper(f):
        config.builder().with_function(f).build().run()
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


def builder():
    return _demobuilder()


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
        return f"arguments({formatters.args_string(self.args, self.kwargs)})"

    def __str__(self):
        return repr(self)


run_result = namedtuple('run_result', ['function', 'arguments', 'return_value'])


class _demobase:
    __slots__ = '_functions', '_groups', '_arguments', '_options', '_formatter'

    def __init__(self, *, functions, groups, args, options, formatter):
        self._functions = functions
        self._groups = groups
        self._arguments = args
        self._options = options
        self._formatter = formatter

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
            f"<{self.__class__.__name__} object with {len(self._functions)} function(s) | "
            f"groups={self._groups}, arguments={self._arguments}, "
            f"options={self._options}, formatter={self._formatter}>"
        )

    def __eq__(self, other):
        return NotImplemented

    def __ne__(self, other):
        return NotImplemented


class _demobuilder(_demobase):

    def __init__(self):
        super().__init__(
            functions=[],
            groups=set(),
            args=[],
            options=_default_options.copy(),
            formatter=_default_formatter)

    def build(self):
        """Create a demo object using the current configuration."""
        return _demo._copy_of(self)

    def with_function(self, *funcs):
        """Add the specified function to the run configuration."""
        self._functions += list(funcs)
        return self

    def with_group(self, *groups):
        """Add the specified group to the run configuration."""
        self._groups |= set(groups)
        return self

    def with_args(self, *args, **kwargs):
        """Add the specified argument configuration to the run configuration."""
        if len(args) > 0 and all(isinstance(arg, arguments) for arg in args):
            self._arguments += list(args)
        else:
            self._arguments += [arguments(*args, **kwargs)]
        return self

    def with_args_iter(self, iterable):
        """Add the specified arguments to the run configuration.

        Intended for use with generator expressions."""
        all_args = []

        for element in iterable:
            if not isinstance(element, arguments):
                raise DemoStateError("with_args_iter only accepts objects of type argument")
            all_args.append(element)

        self._arguments += all_args
        return self

    def with_formatter(self, formatter):
        """Use the specified formatter for this run configuration."""
        self._formatter = copy.copy(formatter)
        return self

    def with_options(self, **options):
        """Add the specified options to the run configuration."""
        self._options.update(options)
        return self

    def __getstate__(self):
        return (
            _serialize_protocol_version,
            (self._arguments, self._options, self._formatter)
        )

    def __setstate__(self, state):
        self.__init__()
        version, data = state
        if version != _serialize_protocol_version:
            raise Warning("Different serialization protocol version detected. "
                          "Importing may produce unexpected results.")
        self._arguments, self._options, self._formatter = data

    def store(self, file):
        """Store this run configuration in the specified file."""
        if isinstance(file, str):
            with open(file, 'wb') as actual_file:
                pickle.dump(self, actual_file)
        else:
            pickle.dump(self, file)


class _demo(_demobase):

    def builder(self):
        """Create a mutable builder from the current object state."""
        return _demobuilder._copy_of(self)

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


def load(file):
    """Deserialize the run configuration from the specified file."""
    if isinstance(file, str):
        with open(file, 'rb') as actual_file:
            return pickle.load(actual_file)
    return pickle.load(file)
