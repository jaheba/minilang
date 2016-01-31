
'''
    Notes:
    variable lookups cause a real dictionary lookup each time (including hashing)

'''

import os, sys

DEBUG = os.environ.get('DEBUG', None)
def debug(text):
    if DEBUG:
        print >> sys.stderr, text

from rpython.rlib.jit import JitDriver, purefunction, hint

# meta programming
op_codes = {}

for i, name in enumerate('''STORE CONST_INT STRING POP LOAD_VAR JUMP JNE COMP PLUS SUB MUL DIV CALL
MAKE_FUNC RETURN ARG ARG_COUNT PRINT CREATE_LIST GETITEM SETITEM SWAPITEM ATTRIBUTE'''.split()):
    globals()[name] = i
    op_codes[name] = i

op_names = op_codes.keys()

class Object(object):
    __slots__ = 'i_value', 's_value', 'bool', 'namespace', 'address', 'arguments', 'list'
    _immutable_fields_ = 'i_value', 's_value', 'bool'

    def to_str(self):
        return '<Empty Object>'


class Integer(Object):
    _immutable_fields_ = "i_value",

    def __init__(self, value):
        # assert type(value) is int
        self.i_value = value

    def _bool(self, bool):
        if bool:
            return w_True
        else:
            return w_False

    def eq(self, other):
        return self._bool(self.i_value == other.i_value)

    def ne(self, other):
        return self._bool(self.i_value != other.i_value)

    def lt(self, other):
        return self._bool(self.i_value < other.i_value)

    def le(self, other):
        return self._bool(self.i_value <= other.i_value)

    def gt(self, other):
        return self._bool(self.i_value > other.i_value)

    def ge(self, other):
        return self._bool(self.i_value >= other.i_value)

    # calc

    def add(self, other):
        return Integer(self.i_value + other.i_value)
    
    def sub(self, other):
        return Integer(self.i_value - other.i_value)

    def mul(self, other):
        return Integer(self.i_value * other.i_value)
    
    def div(self, other):
        return Integer(self.i_value / other.i_value)

    def to_str(self):
        return str(self.i_value)

class String(Object):
    _immutable_fields_ = "s_value",

    def __init__(self, value):
        self.s_value = value

    def to_str(self):
        return self.s_value

    def add(self, other):
        return other.ladd_string(self.s_value)

    def ladd_string(self, other):
        return String(other + self.s_value)

class List(Object):

    def __init__(self, list):
        self.list = list

    def _check_bounds(self, index):
        if index  >= len(self.list):
            raise IndexError('%s not <= %s' %(index, len(self.list)))

    def getitem(self, w_index):
        index = w_index.i_value
        self._check_bounds(index)
        return self.list[index]

    def setitem(self, w_index, w_object):
        index = w_index.i_value
        self._check_bounds(index)
        self.list[index] = w_object

    def to_str(self):
        return '[%s]' %(', '.join(item.to_str() for item in self.list))

    def attribute(self, name):
        if name == 'length':
            return Integer(len(self.list))
        else:
            raise AttributeError('uknown attribute %s' %name)


class Bool(Object):
    _immutable_fields_ = "bool",

    def __init__(self, bool):
        self.bool = bool

    def bool_value(self):
        return self.bool

    def to_str(self):
        if self.bool:
            return 'True'
        else:
            return 'False'

w_True = Bool(True)
w_False = Bool(False)


class Function(Object):
    def __init__(self, address, arguments, namespace):
        self.address = address
        self.arguments = arguments
        self.namespace = namespace

    def to_str(self):
        return '<fn at %s>' %self.address

def get_location(pc, program, program_args):
    inst = program[pc]
    arg = program_args[pc]
    return 'PC: %s: %s with arg %s' %(pc, op_names[inst], arg.to_str())

jitdriver = JitDriver(greens=['pc', 'program', 'program_args'], reds=['interpreter'],
        get_printable_location=get_location)


RECURSION_DEPTH = 200

from core import Namespace

class Interpreter(object):
    _immutable_fields_ = ("program[*]", "program_args[*]")
    def __init__(self, program, program_args):
        self.stack = [Object()] * 100
        self.stack_ptr = 0
        self.program = program
        self.program_args = program_args

        self.call_stack_ptr = 0
        self.call_stack = [0] * RECURSION_DEPTH

        self.namespace = Namespace()

    def next(self, pc):
        if pc >= len(self.program):
            return -1

        instruction = self.program[pc]
        arg = self.program_args[pc]

        debug('%s with %s' %(op_names[instruction], arg.to_str()))

        # variables / consts
        if instruction == STORE:
            self.STORE(arg.s_value)
        elif instruction == CONST_INT:
            self.CONST_INT(arg)
        elif instruction == STRING:
            self.STRING(arg)
        elif instruction == LOAD_VAR:
            self.LOAD_VAR(arg.s_value)

        elif instruction == POP:
            self.POP()

        # jump stuff
        elif instruction == JUMP:
            pc = self.JUMP(arg.i_value)
        elif instruction == JNE:
            pc = self.JNE(arg.i_value, pc)
        
        elif instruction == COMP:
            self.COMP(arg.s_value)

        # calc
        elif instruction == PLUS:
            self.PLUS(arg)
        elif instruction == SUB:
            self.SUB(arg)
        elif instruction == MUL:
            self.MUL(arg)
        elif instruction == DIV:
            self.DIV(arg)

        elif instruction == PRINT:
            self.PRINT()
        
        elif instruction == CREATE_LIST:
            self.CREATE_LIST(arg.i_value)
        elif instruction == GETITEM:
            self.GETITEM()
        elif instruction == SETITEM:
            self.SETITEM()
        elif instruction == SWAPITEM:
            self.SWAPITEM()

        elif instruction == ATTRIBUTE:
            self.ATTRIBUTE(arg.s_value)

        # function definition
        elif instruction == ARG:
            self.ARG(arg)
        elif instruction == ARG_COUNT:
            self.ARG_COUNT(arg)
        elif instruction == MAKE_FUNC:
            self.MAKE_FUNC(arg.s_value, pc)
        elif instruction == CALL:
            pc = self.CALL(arg.i_value, pc)
        elif instruction == RETURN:
            pc = self.RETURN(arg.i_value)

        else:
            raise ValueError('opcode %s not yet implemented' %op_names[instruction])

        pc += 1
        return pc

    def run(self):
        pc = 0
        while True:
            jitdriver.jit_merge_point(
                pc=pc, program=self.program, program_args=self.program_args,
                interpreter=self)
            
            pc = self.next(pc)
            if pc == -1:
                break

    def _stack_pop_two(self):
        return self.stack_pop(), self.stack_pop()

    def stack_push(self, value):
        self.stack[self.stack_ptr] = value
        self.stack_ptr += 1

    def stack_pop(self):
        self.stack_ptr -= 1
        return self.stack[self.stack_ptr]

    def call_stack_push(self, address):
        self.call_stack[self.call_stack_ptr] = address
        self.call_stack_ptr += 1

    def call_stack_pop(self):
        self.call_stack_ptr -= 1
        return self.call_stack[self.call_stack_ptr]

    # byte codes

    def POP(self, arg=None):
        self.stack_pop()

    def LOAD_VAR(self, name):
        self.stack_push(self.namespace.get(name))

    def CONST_INT(self, value):
        self.stack_push(value)

    def STRING(self, value):
        self.stack_push(value)

    def STORE(self, name):
        value = self.stack_pop()
        self.namespace.set(name, value)


    def JUMP(self, pc):
        return pc - 1

    def JNE(self, pc, old_pc):
        value = self.stack_pop()

        if value is w_False:
            return self.JUMP(pc)
        return old_pc

    def COMP(self, op):
        b = self.stack_pop()
        a = self.stack_pop()

        if op == '==':
            self.stack_push(a.eq(b))
        elif op == '!=':
            self.stack_push(a.ne(b))
        elif op == '<':
            self.stack_push(a.lt(b))
        elif op == '<=':
            self.stack_push(a.le(b))
        elif op == '>':
            self.stack_push(a.gt(b))
        elif op == '>=':
            self.stack_push(a.ge(b))
        else:
            raise ValueError(op)

    def SUB(self, _=None):
        b, a = self._stack_pop_two()
        self.stack_push(a.sub(b))

    def PLUS(self, _=None):
        b, a = self._stack_pop_two()
        self.stack_push(a.add(b))

    def MUL(self, _=None):
        b, a = self._stack_pop_two()
        self.stack_push(a.mul(b))

    def DIV(self, _=None):
        b, a = self._stack_pop_two()
        self.stack_push(a.div(b))

    def ARG(self, arg):
        self.stack_push(arg)

    def ARG_COUNT(self, arg):
        self.stack_push(arg)

    def MAKE_FUNC(self, name, pc):
        count = self.stack_pop().i_value

        args = [self.stack_pop().s_value for _ in range(count)]
        args.reverse()

        self.namespace.set(name, Function(
            address=pc + 1,
            arguments=args,
            namespace=Namespace(self.namespace)
        ))

    def CALL(self, argcount, pc):
        func = self.stack_pop()
        args = [self.stack_pop() for _ in range(argcount)]
        args.reverse()

        self.call_stack_push(pc)
        self.namespace = Namespace(self.namespace)
        pc = func.address

        for i, name in enumerate(func.arguments):
            value = args[i]
            self.namespace.set(name, value)

        return pc

    def RETURN(self, has_value):
        if not has_value:
            self.stack_push(Integer(0))

        self.namespace = self.namespace.parent

        pc = self.call_stack_pop()
        return pc

    def PRINT(self):
        o = self.stack_pop()
        print o.to_str()

    def CREATE_LIST(self, size):
        items = [self.stack_pop() for _ in range(size)]
        self.stack_push(List(items))

    def GETITEM(self):
        o = self.stack_pop()
        selector = self.stack_pop()
        self.stack_push(o.getitem(selector))

    def SETITEM(self):
        o = self.stack_pop()
        selector = self.stack_pop()
        value = self.stack_pop()
        o.setitem(selector, value)
        self.stack_push(o)

    def SWAPITEM(self):
        o = self.stack_pop()
        left = self.stack_pop()
        right = self.stack_pop()
        old_left = o.getitem(left)
        old_right = o.getitem(right)
        o.setitem(left, old_right)
        o.setitem(right, old_left)

        self.stack_push(o)

    def ATTRIBUTE(self, name):
        o = self.stack_pop()
        self.stack_push(o.attribute(name))
