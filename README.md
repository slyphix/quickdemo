## quickdemo

_For when unit tests would be too much!_

`quickdemo` is a tiny Python library for code demonstrations and small-scale testing.
If your debugging tool of choice is printing to `stdout`, this might be the right library for you.

`quickdemo` allows you to decorate any module-level function with an _invocation_ or _testing_ directive:

    import quickdemo as qd

    @qd.expect([1, 2], [0, 1], 1)
    @qd.run([1, 2, 3], 5)
    def add_to_list(input_list, number):
        return [x + number for x in input_list]

The snippet above produces the following output:

    add_to_list([1, 2, 3], 5) -> [6, 7, 8]
    Passed: add_to_list([0, 1], 1)

Check out the `showcase*.py` files for more examples!

I developed `quickdemo` for two reasons:

Firstly, when presenting solutions to other people, I always wrote several `print` statements per function to demonstrate the correctness of the solution.
The `print` statements always added up quickly, making it difficult to discern which output corresponded to which function.
Also, changing any function name implied re-writing the invocation code.
This was especially tedious when working with Jupyter Notebooks, where you have to take great care to re-run a cell each time something changes.

Secondly, there is an educational programming language called [Pyret](https://www.pyret.org/), which allows writing short unit tests as part of a function definition.
I believe this to be a sensible choice when targeting beginners.
Unfortunately, Pyret code is neither readable nor particularly fast, so I decided to introduce this feature to Python as a part of `quickdemo`.
