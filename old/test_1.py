my_list = []

def add_to_list(x, the_list=my_list):
    the_list.append(x)

def print_list():
    print(f"Inside test_1 file: {my_list} , id: {id(my_list)}")

def assign_list():
    global my_list
    my_list = ["assigned list"]
