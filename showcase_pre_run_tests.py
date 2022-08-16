import math

import quickdemo as qd

from dataclasses import dataclass


# Use quickdemo during development to assert that every test passed before running the main program
qd.exit_on_test_failure(True)
# Suppress the output prints if you do not want them
qd.disable_output(False)


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def dist(self, other):
        return math.hypot(self.x - other.x, self.y - other.y)


# Unfortunately, you cannot reference a class from within itself :c
# Use this workaround for now!
qd.expect(5, Point(2, 2), Point(5, 6))(Point.dist)


# Use expect_any and expect_error to check Exception behavior
@qd.expect([(1, 2), (2, 3)], [1, 2, 3])
@qd.expect_any([0] * 100)
@qd.expect_error(ValueError, [])
@qd.expect_error(ValueError, [1])
def pairwise(seq):
    if len(seq) < 2:
        raise ValueError("not enough elements to form pairs")
    return list(zip(seq, seq[1:]))


def main():
    points = [Point(0, 0), Point(5, 7), Point(3, 2), Point(9, 1)]
    total_distance = sum(x.dist(y) for x, y in pairwise(points))
    print(total_distance)


# Optional: Output a test summary!
qd.print_test_summary()


if __name__ == '__main__':
    main()
