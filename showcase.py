import quickdemo as qd


@qd.group(1, 'simple')
@qd.run([1, 2, 3], 5)
def add_to_list(input_list, number):
    return [x + number for x in input_list]


@qd.group(1)
def add_to_list_alt(input_list, number):
    output_list = []
    for i in range(len(input_list)):
        output_list.append(input_list[i] + number)
    return output_list


# select one or multiple groups for batch execution
builder = qd.builder().with_group(1).with_args([2] * 10, 20).with_formatter(qd.formatters.result_printer)
simple_printer = builder.build()

# re-use existing configurations
fancy_printer = builder.with_formatter(qd.formatters.fancy_printer).build()

# execute configurations later
simple_printer.run()
fancy_printer.run()

# run elaborate setup tasks once ...
long_list = list(range(100))
long_list[20:30] = range(10)

# ... and store configuration for later
qd.builder().with_args(long_list, 1).store("config.qdc")
qd.load("config.qdc").with_group('simple').build().run()
