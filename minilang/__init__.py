import sys

from grammar import parse
from bytecode import ByteCodeCompiler

def compile(text):
    ast = parse(text)
    print >> sys.stderr, ast
    cc = ByteCodeCompiler()
    cc.compile(ast)
    return cc.program


if __name__ == '__main__':
    from interpreter import run

    with open(sys.argv[1]) as fobj:
        text = fobj.read()

    program = compile(text)
    run(program)