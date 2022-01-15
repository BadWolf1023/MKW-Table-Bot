from test_1 import add_to_list
import test_1

def print_list():
    print(f"Main test file: {test_1.my_list}, id: {id(test_1.my_list)}")


print_list()
test_1.print_list()
print()

add_to_list("Hello world")
print_list()
test_1.print_list()
print()

test_1.assign_list()
print_list()
test_1.print_list()
print()

add_to_list("Hello world")
print_list()
test_1.print_list()
