'''
Created on Aug 5, 2020

@author: willg
'''



if __name__ == "__main__":
    print("{", end="")
    with open("example_chars.txt", encoding="utf-8", errors="replace") as f:
        for line in f:
            c, value = line.split()
            real_string = None
            if '\\\\u' not in str(c.encode('ascii', 'backslashreplace')):
                real_string = "\\u00" + str(c.encode('ascii', 'backslashreplace')).replace("b'\\\\", "").replace("'", "").replace("x", "")
            else:
                real_string = "\\" + str(c.encode('ascii', 'backslashreplace')).replace("b'\\\\", "").replace("'", "").replace("x", "")
            print('"' + real_string[:2] + real_string[2:].upper() + '":"' + value + '",', end=" ")
    print("}")