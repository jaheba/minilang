
from interpreter import Instruction

from collections import namedtuple

LabeledInstruction = namedtuple(
    'LabeledInstruction',
    ['code', 'arg', 'lookup']
)


class ByteCodeCompiler(object):
    def __init__(self):
        self.program = []
        self.labels = []
        self.labels_end = []

    def compile(self, ast):
        self.eval_block(ast)
        self._resolve_labels()

    def eval_block(self, ast):
        for node in ast:
            bc_name = type(node).__name__
            self.eval(node)
            if bc_name not in ['ASSIGN', 'LOOP']:
                self.pop()

        return self.program

    def _resolve_labels(self):
        for index, inst in enumerate(self.program):
            if type(inst) == LabeledInstruction:
                arg = inst.lookup[inst.arg]

                self.program[index] = Instruction(
                    code=inst.code,
                    arg=arg
                )

    def pop(self):
        self.program.append(
            Instruction('POP', None)
        )

    def next_label(self):
        index = len(self.labels)
        self.labels.append(len(self.program))
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
        self.program.append(
            Instruction('STORE', node.name)
        )

    def CONST_INT(self, node):
        self.program.append(
            Instruction('CONST_INT', node.value)
        )

    def LOAD_VAR(self, node):
        self.program.append(
            Instruction('LOAD_VAR', node.name)
        )

    def LOOP(self, node):
        label = self.next_label()

        # eval condition
        self.eval(node.condition)

        # decide to jump or not
        self.program.append(
            LabeledInstruction('JNE', label, self.labels_end)
        )

        # if no jump has happened, execute loop body
        self.eval_block(node.body)
        # jump back (body end)
        self.program.append(
            Instruction('JUMP', self.labels[label])
        )

        self.mark_label_end(label)

    def BINOP(self, node):
        self._eval_left_right(node)

        if node.type == '<':
            self.program.append(
                Instruction('COMP', 'LE')
            )
        elif node.type == '+':
            self.program.append(
                Instruction('PLUS', None)
            )
        else:
            raise ValueError(node.type)

    def CALL(self, node):
        for arg in node.args[::-1]:
            self.eval(arg)

        self.eval(node.name)
        self.program.append(
            Instruction('CALL', len(node.args))
        )


text = 'x:=0; while x < 5 { print(x); x := x+1; }'

from grammar import parse
from interpreter import Intepreter, run

from pprint import pprint
# i = Intepreter()

ast = parse(text)
# pprint(ast)

bcc = ByteCodeCompiler()

bcc.compile(ast)

i = run(bcc.program)

# print i.namespace
