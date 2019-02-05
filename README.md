### quickdemo - For When Unit Tests Would Be Too Much

*Work In Progress - Interfaces might change in the future!*

`quickdemo` is a tiny python library for quick prototyping and code
demonstrations. If your debugging tool of choice is printing to `stdout`,
this might well be the right library for you.

There may be times when you only need to demonstrate that a function works on
a few well-chosen inputs. In that case, it might suffice to just call the
function with your test input and print the results.

However, during early prototyping your function interface might change very
rapidly and you would have to adjust your print statement every time your
function call changes. Or perhaps you would like to provide multiple
equivalent implementations of the same function that share the same signature
and run all your test on all of them.

Fortunately, there is a way to ease this tedious task.
`quickdemo` offers function decorators that will call the decorated function
using the supplied arguments when the file is run and print the result (if any).
