

import os.path
import subprocess

import re
import click
import glob

from minilang.translate import to_bytecode

basepath = os.path.dirname(os.path.abspath(__file__))

def compile_mm(path):

    with open(path+'c', 'w') as fobj:
        fobj.write(to_bytecode(path))

def multitime(cmd, n=1):
    print  ' '.join(['multitime', '-n', str(n)] + cmd)
    subprocess.call(['multitime', '-n', str(n)] + cmd)

def bench_mm(target):
    interpreter = os.path.join(basepath, '..', 'target-c')
    multitime([interpreter, os.path.abspath(target)])

def bench_pypy(target):
    multitime(['pypy', target])

def bench_cpython(target):
    multitime(['/usr/bin/python', target])


COMPILING = click.style('Compiling: ', fg='yellow')
BENCHING = click.style('Benchmarking: ', fg='cyan')

def bench(name):
    py_path = os.path.join(basepath, 'py', name + '.py')
    mm_path = os.path.join(basepath, 'mm', name + '.mm')
    mmc_path = mm_path + 'c'

    click.echo(COMPILING + '%s.mm' %name)
    compile_mm(mm_path)

    # mm
    print
    click.echo(BENCHING + name + ' (mm)')
    bench_mm(mmc_path)

    # pypy
    print
    click.echo(BENCHING + name + '(PyPy)')
    bench_pypy(py_path)

    # cpython
    print
    click.echo(BENCHING + name + '(CPython)')
    bench_cpython(py_path)

@click.command()
@click.argument('name')
def cli(name):
    if re.match('\d+', name):
        try:
            path = glob.glob(os.path.join(basepath, 'mm', name + '-*.mm'))[0]
            b_name = os.path.basename(path).rsplit('.', 1)[0]
            bench(b_name)
        except IndexError:
            print 'No matching benchmark ' + name

if __name__ == '__main__':
    cli()