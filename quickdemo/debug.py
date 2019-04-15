"""debug submodule - Provides useful helpers for quick debugging."""

from io import StringIO

_indent_width = 4
_indent_depth = 0


def set_indent_width(width):
    global _indent_width
    _indent_width = width


def reset_indent_depth():
    global _indent_depth
    _indent_depth = 0


def indent():
    global _indent_depth
    _indent_depth += 1


def dedent():
    global _indent_depth
    _indent_depth = max(0, _indent_depth - 1)


def print_indented(*args, **kwargs):
    global _indent_depth
    file = kwargs.pop('file', None)
    buf = StringIO()
    print(*args, file=buf, **kwargs)
    padded = '\n'.join(' ' * _indent_depth + line for line in buf.getvalue().rstrip().split('\n'))
    print(padded, file=file, end='\n')


def catch(f):
    """Decorator for gracefully catching exceptions on top-level statements."""
    def wrapper(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
        except Exception as ex:
            return str(ex)
        return str(result)
    return wrapper


def with_indent(delta=4):
    def builder(f):
        def wrapper(*args, **kwargs):
            global _indent_depth
            _indent_depth += delta
            result = f(*args, **kwargs)
            _indent_depth -= delta
            return result
        return wrapper
    return builder
