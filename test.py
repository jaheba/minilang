
import os.path
from glob import glob
from minilang.translate import to_bytecode



basepath = os.path.dirname(os.path.abspath(__file__))
testpath = os.path.join(basepath, 'tests')


def compile_mm(path):

    with open(path+'c', 'w') as fobj:
        fobj.write(to_bytecode(path))

def compile_all():
    for path in glob(os.path.join(testpath, '*.mm')):
        compile_mm(path)


def test():
    pass