
'''
    Notes:
    variable lookups cause a real dictionary lookup each time (including hashing)

'''

import os
import sys

from rpython.rlib import jit
from rpython.rlib.jit import JitDriver

from rpin.core import Namespace
from rpin.exceptions import Panic
from rpin.types import Object, Integer, String, List, Function, Bool, w_True, w_False


DEBUG = os.environ.get('DEBUG', None)

def debug(text):
    if DEBUG:
        print >> sys.stderr, text


# meta programming
op_codes = {}

for i, name in enumerate('''STORE_LOCAL STORE_GLOBAL CONST_INT STRING POP LOAD_LOCAL LOAD_GLOBAL JUMP JNE COMP
PLUS SUB MUL DIV MODULUS CALL ASSERT MAKE_FUNC RETURN ARG ARG_COUNT PRINT CREATE_LIST
GETITEM SETITEM SWAPITEM ATTRIBUTE CALL_METHOD LOAD_METHOD
NEW_STRUCT STRUCT_TYPE STRUCT_FIELD'''.split()):
    globals()[name] = i
    op_codes[name] = i

op_names = op_codes.keys()


def get_location(pc, code):
    inst = code.program[pc]
    arg = code.program_args[pc]
    return 'PC: %s: %s with arg %s' % (pc, op_names[inst], arg.to_str())

class MyJitDriver(JitDriver):
    greens = ['pc', 'code']
    reds = ['interpreter']
    virtualizables = ['interpreter']

jitdriver = MyJitDriver(get_printable_location=get_location)


RECURSION_DEPTH = 200


class Code(object):
    _immutable_fields_ = ("program[*]", "program_args[*]", "length")

    def __init__(self, program, program_args):
        self.program = program
        self.program_args = program_args
        self.length = len(self.program)


class Interpreter(object):
    _virtualizable_ = ["code", "locals[*]", "stack_ptr"]

    def __init__(self, code, globals=None, locals=None, stack_depth=0, pc=0):
        self = jit.hint(self, access_directly=True, fresh_virtualizable=True)
        self.start_pc = pc
        self.code = code

        if not stack_depth:
            stack_depth = self.init_stack_depth()

        if locals is None:
            locals = []
        
        self.stack_ptr = len(locals)
        self.min_stack_ptr = len(locals)
        self.locals = locals + [None] * stack_depth

        if globals is None:
            self.globals = Namespace()
            self.globals.set('true', w_True)
            self.globals.set('false', w_False)
        else:
            self.globals = globals

    def init_stack_depth(self):
        arg = self.code.program_args[0]
        assert isinstance(arg, Integer)
        self.start_pc += 1
        return arg.i_value

    def next(self, pc):
        jit.promote(self.code)
        jit.promote(pc)

        if pc >= self.code.length:
            return -1

        instruction = self.code.program[pc]
        arg = self.code.program_args[pc]

        debug('%s with %s' %(op_names[instruction], arg.to_str()))

        # variables / consts
        if instruction == STORE_GLOBAL:
            assert isinstance(arg, String)
            self.STORE_GLOBAL(arg.s_value)

        elif instruction == LOAD_GLOBAL:
            assert isinstance(arg, String)
            self.LOAD_GLOBAL(arg.s_value)

        elif instruction == STORE_LOCAL:
            assert isinstance(arg, Integer)
            self.STORE_LOCAL(arg.i_value)

        elif instruction == LOAD_LOCAL:
            assert isinstance(arg, Integer)
            self.LOAD_LOCAL(arg.i_value)

        elif instruction == CONST_INT:
            assert isinstance(arg, Integer)
            self.CONST_INT(arg)

        elif instruction == STRING:
            assert isinstance(arg, String)
            self.STRING(arg)

        elif instruction == POP:
            self.POP()

        # jump stuff
        elif instruction == JUMP:
            assert isinstance(arg, Integer)
            target = self.JUMP(arg.i_value)
            # if target < pc:
                # jitdriver.can_enter_jit(pc=pc, program=self.program,
                    # program_args=self.program_args, interpreter=self)
            pc = target

        # jumps always forwards
        elif instruction == JNE:
            assert isinstance(arg, Integer)
            pc = self.JNE(arg.i_value, pc)

        elif instruction == COMP:
            assert isinstance(arg, String)
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
        elif instruction == MODULUS:
            self.MODULUS(arg)

        elif instruction == PRINT:
            self.PRINT()
        elif instruction == ASSERT:
            self.ASSERT()

        elif instruction == CREATE_LIST:
            assert isinstance(arg, Integer)
            self.CREATE_LIST(arg.i_value)
        elif instruction == GETITEM:
            self.GETITEM()
        elif instruction == SETITEM:
            self.SETITEM()
        elif instruction == SWAPITEM:
            self.SWAPITEM()

        elif instruction == ATTRIBUTE:
            assert isinstance(arg, String)
            self.ATTRIBUTE(arg.s_value)

        # function definition
        elif instruction == ARG:
            self.ARG(arg)
        elif instruction == ARG_COUNT:
            self.ARG_COUNT(arg)
        elif instruction == MAKE_FUNC:
            assert isinstance(arg, String)
            self.MAKE_FUNC(arg.s_value, pc)
        elif instruction == CALL:
            assert isinstance(arg, Integer)
            self.CALL(arg.i_value, pc)
        elif instruction == RETURN:
            assert isinstance(arg, Integer)
            pc = self.RETURN(arg.i_value)

        elif instruction == LOAD_METHOD:
            self.LOAD_METHOD(arg)
        elif instruction == CALL_METHOD:
            assert isinstance(arg, Integer)
            self.CALL_METHOD(arg.i_value)

        # elif instruction == NEW_STRUCT:
            # assert isinstance(arg, String)
            # self.NEW_STRUCT(arg.s_value)

        # elif instruction == STRUCT_TYPE:
        #     self.STRUCT_TYPE(arg)

        # elif instruction == STRUCT_FIELD:
        #     self.STRUCT_TYPE(arg)

        else:
            raise ValueError('opcode %s not yet implemented' %op_names[instruction])

        pc += 1
        return pc

    def run(self):
        pc = self.start_pc
        try:
            while True:
                jitdriver.jit_merge_point(
                    pc=pc, code=self.code,
                    interpreter=self)

                oldpc = pc
                pc = self.next(pc)
                
                if pc == -1:
                    break
                elif pc < oldpc:
                    jitdriver.can_enter_jit(pc=pc, code=self.code, interpreter=self)

        except Panic as e:
            print 'PANIC: ' + str(e)
            return 1
        return 0

    def _stack_pop_two(self):
        return self.stack_pop(), self.stack_pop()

    def stack_push(self, value):
        jit.promote(self.stack_ptr)
        index = self.stack_ptr
        assert index >= 0
        self.locals[index] = value
        self.stack_ptr += 1

    def stack_pop(self):
        jit.promote(self.stack_ptr)
        self.stack_ptr -= 1
        index = self.stack_ptr
        assert index >= 0
        assert index >= self.min_stack_ptr
        result = self.locals[index]
        self.locals[index] = None
        return result

    # byte codes

    def POP(self, arg=None):
        self.stack_pop()

    def LOAD_GLOBAL(self, name):
        self.stack_push(self.globals.get(name))

    def STORE_GLOBAL(self, name):
        value = self.stack_pop()
        self.globals.set(name, value)

    def LOAD_LOCAL(self, index):
        assert index >= 0
        self.stack_push(self.locals[index])

    def STORE_LOCAL(self, index):
        assert index >= 0
        self.locals[index] = self.stack_pop()

    def CONST_INT(self, value):
        self.stack_push(value)

    def STRING(self, value):
        self.stack_push(value)

    def JUMP(self, pc):
        return pc - 1

    def JNE(self, pc, old_pc):
        value = self.stack_pop()

        if not value.to_bool():
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

    def MODULUS(self, _=None):
        b, a = self._stack_pop_two()
        self.stack_push(a.mod(b))

    def ARG(self, arg):
        self.stack_push(arg)

    def ARG_COUNT(self, arg):
        self.stack_push(arg)

    def MAKE_FUNC(self, name, pc):
        w_count = self.stack_pop()
        assert isinstance(w_count, Integer)
        count = w_count.i_value

        w_count = self.stack_pop()
        assert isinstance(w_count, Integer)
        locals_count = w_count.i_value

        w_count = self.stack_pop()
        assert isinstance(w_count, Integer)
        stack_depth = w_count.i_value


        args = []
        for _ in range(count):
            w_arg_name = self.stack_pop()
            assert isinstance(w_arg_name, String)
            args.append(w_arg_name.s_value)

        args.reverse()


        #XXX
        self.globals.set(name, Function(
            address=pc + 1,
            arguments=args,
            locals_count=locals_count,
            stack_depth=stack_depth
        ))

    @jit.unroll_safe
    def CALL(self, argcount, pc):
        w_func = self.stack_pop()
        assert isinstance(w_func, Function)

        locals = [None] * w_func.locals_count
        for i in range(argcount-1, -1, -1):
            locals[i] = self.stack_pop()

        interpreter = Interpreter(self.code, self.globals, locals,
            stack_depth=w_func.stack_depth,
            pc=w_func.address+1)

        rc = interpreter.run()

        self.stack_push(interpreter.stack_pop())

    def RETURN(self, has_value):
        if not has_value:
            self.stack_push(Integer(0))

        return self.code.length

    def LOAD_METHOD(self, name):
        self.stack_push(name)

    @jit.unroll_safe
    def CALL_METHOD(self, argcount):
        w_method_name = self.stack_pop()
        assert isinstance(w_method_name, String)
        method_name = w_method_name.s_value

        w_obj = self.stack_pop()

        args = [self.stack_pop() for _ in range(argcount)]
        args.reverse()

        result = w_obj.call_method(method_name, args)
        self.stack_push(result)

    def PRINT(self):
        o = self.stack_pop()
        print o.to_str()

    @jit.unroll_safe
    def CREATE_LIST(self, size):
        w_list = List()
        for _ in range(size):
            w_list.append(self.stack_pop())

        self.stack_push(w_list)

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

    def ASSERT(self):
        if not self.stack_pop().to_bool():
            raise Panic('Assertion failed')

    # STRUCT_TYPE = LOAD_METHOD
    # STRUCT_FIELD = LOAD_METHOD

    # def NEW_STRUCT(self, name):
    #     w_arg = self.stack_pop()
    #     assert isinstance(w_arg, Integer)
    #     argcount = w_arg.i_value

    #     for _ in range(argcount):
    #         name = self.stack_pop()
    #         type_ = self.stack_pop()

    #         if type_ == 'None':
    #             pass


