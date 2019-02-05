"""debug submodule - Provides useful helpers for quick debugging."""

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


def show(*args):
    global _indent_depth, _indent_width
    print(" " * _indent_width * _indent_depth, *args, sep='')


def catch(f):
    """Decorator for gracefully catching exceptions on top-level statements."""
    def wrapper(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
        except Exception as ex:
            return str(ex)
        return str(result)
    return wrapper
