from __future__ import print_function

from collections import namedtuple

Instruction = namedtuple('Instruction', ['code', 'arg'])


class Intepreter(object):
    def __init__(self):
        self.stack = []
        self.namespace = {}
        self.program = []
        self.pc = -1

    def __iter__(self):
        return self

    def next(self):
        self.pc += 1
        try:
            instruction = self.program[self.pc]
        except IndexError:
            raise StopIteration

        func = getattr(self, instruction.code)
        func(instruction.arg)

    def _stack_pop_two(self):
        return self.stack.pop(), self.stack.pop()

    # byte codes

    def POP(self, arg=None):
        self.stack.pop()

    def LOAD_VAR(self, name):
        self.stack.append(self.namespace[name])

    def CONST_INT(self, value):
        self.stack.append(value)

    def STORE(self, name):
        value = self.stack.pop()
        self.namespace[name] = value

    def JUMP(self, address):
        self.pc = address - 1

    def JNE(self, address):
        value = self.stack.pop()

        if not value:
            self.JUMP(address)

    def COMP(self, op):
        b = self.stack.pop()
        a = self.stack.pop()

        if op == 'LE':
            self.stack.append(a < b)
        else:
            raise ValueError(op)

    def MINUS(self):
        b, a = self._stack_pop_two()
        self.stack.append(a - b)

    def PLUS(self, _=None):
        b, a = self._stack_pop_two()
        self.stack.append(a + b)

    def CALL(self, args):
        func = self.stack.pop()
        args = [self.stack.pop() for _ in range(args)][::-1]

        result = func(*args)
        self.stack.append(result)


def run(code):
    i = Intepreter()
    i.program = code
    i.namespace['print'] = lambda *args: print(*args)

    list(i)

    return i
