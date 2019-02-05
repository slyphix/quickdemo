"""formatters submodule - quickdemo output formatters library"""
import itertools

def args_string(args, kwargs):
    args_iter = (str(a) for a in args)
    kwargs_iter = (f'{k}={v}' for k, v in kwargs.items())
    return ', '.join(itertools.chain(args_iter, kwargs_iter))

def fancy_printer(result):
    args = args_string(result.arguments.args, result.arguments.kwargs)
    print(f"{result.function.__name__}({args}) -> {result.return_value}")

def result_printer(result):
    print(result.return_value)
