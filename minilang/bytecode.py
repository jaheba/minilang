
# from interpreter import Instruction

from collections import namedtuple

Instruction = namedtuple('Instruction', ['code', 'arg'])
LabeledInstruction = namedtuple(
    'LabeledInstruction',
    ['code', 'arg']
)

STATEMENTS = ['ASSIGN', 'COND', 'LOOP', 'RET', 'FUNC', 'STRUCT', 'PRINT']

class ByteCodeCompiler(object):
    def __init__(self):
        self.program = [None]
        self.labels = []
        self.labels_end = []
        self.loop_labels = []
        self.if_label = None
        self.block_level = 0
        self.local_vars = {}
        self.stack_depth = 0
        self.max_stack_depth = 0

    def stack_effect(self, offset):
        self.stack_depth += offset
        self.max_stack_depth = max(self.stack_depth, self.max_stack_depth)

    def compile(self, ast):
        self.eval_block(ast)
        self._resolve_labels()
        self.program[0] = Instruction('ARG_COUNT', self.max_stack_depth)

    def eval_block(self, ast, return_only=False):
        if self.block_level > 0:
            for node in ast:
                bc_name = type(node).__name__

                if bc_name == 'ASSIGN':
                    if not node.name in self.local_vars:
                        self.local_vars[node.name] = len(self.local_vars)
                        # self.vars_to_remove.append(node.name)
        if return_only:
            old_program = self.program
            self.program = []
        for node in ast:
            bc_name = type(node).__name__
            self.eval(node)
            if bc_name not in STATEMENTS:
                self.pop()

        if return_only:
            result = self.program
            self.program = old_program
            return result
        else:
            return self.program

    def _resolve_labels(self):
        for index, inst in enumerate(self.program):
            if type(inst) == LabeledInstruction:
                arg = self.labels_end[inst.arg]
                # arg = inst.lookup[inst.arg]

                self.program[index] = Instruction(
                    code=inst.code,
                    arg=arg
                )

    def pop(self):
        self.stack_effect(-1)
        self.program.append(Instruction('POP', None))

    def next_label(self, skip=0):
        index = len(self.labels)
        self.labels.append(len(self.program) + skip)
        self.labels_end.append(None)
        return index

    def mark_label_end(self, index):
        self.labels_end[index] = len(self.program)

    def next_loop_label(self):
        label = self.next_label()
        self.loop_labels.append(label)
        return label

    def mark_loop_label_end(self, index):
        self.mark_label_end(index)
        self.loop_labels.pop()

    def eval(self, node):
        bc_name = type(node).__name__
        func = getattr(self, bc_name)
        func(node)

    def _eval_left_right(self, node):
        self.eval(node.left)
        self.eval(node.right)

    def ASSIGN(self, node):
        self.eval(node.value)
        self.stack_effect(-1)
        
        if self.block_level > 0:
            self.program.append(Instruction('STORE_LOCAL', self.local_vars[node.name]))
        else:
            self.program.append(Instruction('STORE_GLOBAL', node.name))

    def CONST_INT(self, node):
        self.program.append(Instruction('CONST_INT', node.value))
        self.stack_effect(1)

    def STRING(self, node):
        #strip " "
        self.program.append(Instruction('STRING', node.value[1:-1]))
        self.stack_effect(1)


    def LOAD_VAR(self, node):
        if self.block_level > 0 and node.name in self.local_vars:
            self.program.append(Instruction('LOAD_LOCAL', self.local_vars[node.name]))
        else:
            self.program.append(Instruction('LOAD_GLOBAL', node.name))

        self.stack_effect(1)


    def COND(self, node):
        resolve_if = False
        if not self.if_label:
            resolve_if = True
            self.if_label = self.next_label()

        cond_label = self.next_label()

        # eval condition
        self.eval(node.condition)

        # decide to jump or not
        self.program.append(LabeledInstruction('JNE', cond_label))
        self.stack_effect(-1)

        # if no jump has happened, execute if body
        self.eval_block(node.body)
        self.program.append(LabeledInstruction('JUMP', self.if_label))

        self.mark_label_end(cond_label)

        if node.alt:
            self.eval_block(node.alt)

        if resolve_if:
            self.mark_label_end(self.if_label)
            self.if_label = None

    def LOOP(self, node):
        label = self.next_loop_label()

        # eval condition
        self.eval(node.condition)

        # decide to jump or not
        self.program.append(LabeledInstruction('JNE', label))
        self.stack_effect(-1)

        # if no jump has happened, execute loop body
        self.eval_block(node.body)

        # jump back (body end)
        self.CONTINUE()
        # self.program.append(Instruction('JUMP', self.labels[label]))

        self.mark_loop_label_end(label)

    def BREAK(self, node=None):
        label = self.loop_labels[-1]
        self.program.append(LabeledInstruction('JUMP', label))

    def CONTINUE(self, node=None):
        label = self.loop_labels[-1]
        self.program.append(Instruction('JUMP', self.labels[label]))


    def COMP(self, node):
        self._eval_left_right(node)
        self.program.append(Instruction('COMP', node.type))
        self.stack_effect(-1)


    def BINOP(self, node):
        self._eval_left_right(node)

        if node.type == '+':
            self.program.append(Instruction('PLUS', None))
        elif node.type == '-':
            self.program.append(Instruction('SUB', None))
        elif node.type == '*':
            self.program.append(Instruction('MUL', None))
        elif node.type == '/':
            self.program.append(Instruction('DIV', None))
        elif node.type == '%':
            self.program.append(Instruction('MODULUS', None))
        else:
            raise ValueError(node.type)

        self.stack_effect(-1)


    def CALL(self, node):
        for arg in node.args[::-1]:
            self.eval(arg)

        self.eval(node.name)
        self.program.append(Instruction('CALL', len(node.args)))

        #isn't function object also popped?
        self.stack_effect(-len(node.args))


    def METHOD_CALL(self, node):
        for arg in node.args[::-1]:
            self.eval(arg)

        self.eval(node.obj)
        self.program.append(Instruction('LOAD_METHOD', node.method))
        self.program.append(Instruction('CALL_METHOD', len(node.args)))
        self.stack_effect(2-len(node.args))


    def FUNC(self, node):
        self.local_vars = {}

        for arg in node.args[::-1]:
            self.program.append(Instruction('ARG', arg))
            self.local_vars[arg] = len(self.local_vars)
        
        self.stack_effect(len(node.args) + 3)
        # arg_count for stack depth
        self.program.append(None)

        # arg_count for len(local_vars)
        local_vars_index = len(self.program)
        self.program.append(None)
        
        self.program.append(Instruction('ARG_COUNT', len(node.args)))
        self.program.append(Instruction('MAKE_FUNC', node.name))
        
        label = self.next_label(skip=1)
        self.program.append(LabeledInstruction('JUMP', label))

        stack_depth = self.stack_depth
        max_stack_depth = self.max_stack_depth
        self.stack_depth = 0
        self.max_stack_depth = 0

        self.block_level += 1
        self.eval_block(node.body)
        self.block_level -= 1

        func_stack_depth = self.max_stack_depth
        self.stack_depth = stack_depth
        self.max_stack_depth = max_stack_depth

        self.program[local_vars_index] = Instruction('ARG_COUNT', len(self.local_vars))
        self.program[local_vars_index-1] = Instruction('ARG_COUNT', func_stack_depth)

        if not self.program[-1].code == 'RETURN':
            self.program.append(Instruction('RETURN', 0))
            self.stack_effect(1)

        self.mark_label_end(label)

    def RET(self, node):
        self.eval(node.expression)
        self.program.append(Instruction('RETURN', 1))

    def PRINT(self, node):
        self.eval(node.expression)
        self.program.append(Instruction('PRINT', None))
        self.stack_effect(-1)
 
    def ASSERT(self, node):
        self.eval(node.expression)
        self.program.append(Instruction('ASSERT', None))
        self.stack_effect(-1)

    def LIST(self, node):
        for item in node.items[::-1]:
            self.eval(item)
        self.program.append(Instruction('CREATE_LIST', len(node.items)))
        self.stack_effect(1+len(node.items))


    def GETITEM(self, node):
        self.eval(node.selector)
        self.eval(node.target)
        self.program.append(Instruction('GETITEM', None))
        self.stack_effect(-1)

    def SETITEM(self, node):
        self.eval(node.value)
        self.eval(node.selector)
        self.eval(node.target)
        self.program.append(Instruction('SETITEM', None))
        self.stack_effect(-3)

    def SWAPITEM(self, node):
        self.eval(node.right)
        self.eval(node.left)
        self.eval(node.target)
        self.program.append(Instruction('SWAPITEM', None))
        self.stack_effect(-2)


    def ATTRIBUTE(self, node):
        self.eval(node.expression)
        self.program.append(Instruction('ATTRIBUTE', node.name))


    # def STRUCT(self, node):
    #     for field in node.fields:
    #         self.program.append(Instruction('STRUCT_TYPE', field.type))
    #         self.program.append(Instruction('STRUCT_FIELD', field.name))
    #     self.program.append(Instruction('ARG_COUNT', len(node.fields)))
    #     self.program.append(Instruction('NEW_STRUCT', node.name))


# text = 'x:=0; while x < 5 { print(x); x := x+1; }'

from grammar import parse
# from interpreter import Intepreter, run

# from pprint import pprint
# # i = Intepreter()

# ast = parse(text)
# # pprint(ast)

# bcc = ByteCodeCompiler()

# bcc.compile(ast)

# i = run(bcc.program)

# # print i.namespace
