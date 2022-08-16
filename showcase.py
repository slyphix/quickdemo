import quickdemo as qd


# Use quickdemo to annotate functions with instructions and small tests ...
@qd.expect([1, 2], [0, 1], 1)
@qd.run([1], 1)
@qd.run([1, 2, 3], 5)
def add_to_list(input_list, number):
    return [x + number for x in input_list]


# ... or use the composable builder API to prepare a test suite and store it for later
config = qd.builder()\
    .with_actions(qd.Run(qd.Arguments([1, 2, 3], 5)))\
    .with_actions(qd.Run(qd.Arguments([1], 1)))\
    .with_actions(qd.Expect([1, 2], qd.Arguments([0, 1], 1)))\
    .with_options(output_format=qd.VERBOSE_OUTPUT_FORMAT)\
    .with_options(error_format=qd.VERBOSE_ERROR_FORMAT)\
    .build()\
    .store("test.qdc")


@qd.from_file("test.qdc")
def add_to_list_alt(input_list, number):
    output_list = []
    for i in range(len(input_list)):
        output_list.append(input_list[i] + number)
    return output_list
