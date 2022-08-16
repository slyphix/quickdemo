import quickdemo.debug as qdbg


@qdbg.trace
def fib(n):
    print("hello there")
    return n if n <= 1 else fib(n - 1) + fib(n - 2)


def main():
    print(fib(3))
    with qdbg.activate_trace():
        print(fib(3))


if __name__ == '__main__':
    main()

