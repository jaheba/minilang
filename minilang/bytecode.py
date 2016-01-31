
# from interpreter import Instruction

from collections import namedtuple

Instruction = namedtuple('Instruction', ['code', 'arg'])
LabeledInstruction = namedtuple(
    'LabeledInstruction',
    ['code', 'arg']
)

STATEMENTS = ['ASSIGN', 'COND', 'LOOP', 'RET', 'FUNC']

class ByteCodeCompiler(object):
    def __init__(self):
        self.program = []
        self.labels = []
        self.labels_end = []
        self.if_label = None

    def compile(self, ast):
        self.eval_block(ast)
        self._resolve_labels()

    def eval_block(self, ast):
        for node in ast:
            bc_name = type(node).__name__
            self.eval(node)
            if bc_name not in STATEMENTS:
                self.pop()

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
        self.program.append(Instruction('POP', None))

    def next_label(self, skip=0):
        index = len(self.labels)
        self.labels.append(len(self.program) + skip)
        self.labels_end.append(None)
        return index

    def mark_label_end(self, index):
        self.labels_end[index] = len(self.program)

    def eval(self, node):
        bc_name = type(node).__name__
        func = getattr(self, bc_name)
        func(node)

    def _eval_left_right(self, node):
        self.eval(node.left)
        self.eval(node.right)

    def ASSIGN(self, node):

        self.eval(node.value)
        self.program.append(Instruction('STORE', node.name))

    def CONST_INT(self, node):
        self.program.append(Instruction('CONST_INT', node.value))

    def STRING(self, node):
        #strip " "
        self.program.append(Instruction('STRING', node.value[1:-1]))

    def LOAD_VAR(self, node):
        self.program.append(Instruction('LOAD_VAR', node.name))

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
        label = self.next_label()

        # eval condition
        self.eval(node.condition)

        # decide to jump or not
        self.program.append(LabeledInstruction('JNE', label))

        # if no jump has happened, execute loop body
        self.eval_block(node.body)

        # jump back (body end)
        self.program.append(Instruction('JUMP', self.labels[label]))

        self.mark_label_end(label)

    def COMP(self, node):
        self._eval_left_right(node)
        self.program.append(Instruction('COMP', node.type))

    def BINOP(self, node):
        self._eval_left_right(node)

        if node.type == '+':
            self.program.append(Instruction('PLUS', None))

        elif node.type == '-':
            self.program.append(Instruction('SUB', None))
        else:
            raise ValueError(node.type)

    def CALL(self, node):
        for arg in node.args[::-1]:
            self.eval(arg)

        self.eval(node.name)
        self.program.append(Instruction('CALL', len(node.args)))


    def FUNC(self, node):
        for arg in node.args[::-1]:
            self.program.append(Instruction('ARG', arg))

        self.program.append(Instruction('ARG_COUNT', len(node.args)))
        self.program.append(Instruction('MAKE_FUNC', node.name))
        
        label = self.next_label(skip=1)
        self.program.append(LabeledInstruction('JUMP', label))
        
        
        self.eval_block(node.body)

        if not self.program[-1].code == 'RETURN':
            self.program.append(Instruction('RETURN', 0))

        self.mark_label_end(label)

    def RET(self, node):
        self.eval(node.expression)
        self.program.append(Instruction('RETURN', 1))

    def PRINT(self, node):
        self.eval(node.expression)
        self.program.append(Instruction('PRINT', None))

    def LIST(self, node):
        for item in node.items[::-1]:
            self.eval(item)
        self.program.append(Instruction('CREATE_LIST', len(node.items)))

    def GETITEM(self, node):
        self.eval(node.selector)
        self.eval(node.target)
        self.program.append(Instruction('GETITEM', None))

    def SETITEM(self, node):
        self.eval(node.value)
        self.eval(node.selector)
        self.eval(node.target)
        self.program.append(Instruction('SETITEM', None))
    
    def SWAPITEM(self, node):
        self.eval(node.right)
        self.eval(node.left)
        self.eval(node.target)
        self.program.append(Instruction('SWAPITEM', None))

    def ATTRIBUTE(self, node):
        self.eval(node.expression)
        self.program.append(Instruction('ATTRIBUTE', node.name))

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
