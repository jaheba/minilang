


from minilang import compile

import sys

with open(sys.argv[1]) as fobj:
    text = fobj.read()


for inst in compile(text):
    print inst[0], inst[1]