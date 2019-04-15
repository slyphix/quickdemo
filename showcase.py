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


# select a group
qd.demo.with_group(1).with_args([2] * 10, 20).with_formatter(qd.formatters.result_printer).run()

# run elaborate setup once
long_list = list(range(100))
long_list[20:30] = range(10)

# store configuration for later
qd.demo.with_args(long_list, 1).store("config.qdc")
qd.load("config.qdc").with_group('simple').run()
