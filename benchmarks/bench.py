

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
    subprocess.call(['multitime', '-n', str(n)] + cmd)

def bench_mm(target, n, bin):
    multitime([bin, os.path.abspath(target)], n=n)

def bench_pypy(target, n):
    multitime(['pypy', target], n=n)

def bench_cpython(target, n):
    multitime(['/usr/bin/python', target], n=n)


COMPILING = click.style('Compiling: ', fg='yellow')
BENCHING = click.style('Benchmarking: ', fg='cyan')

def bench(name, n=1, bins=None, cpython=False):
    py_path = os.path.join(basepath, 'py', name + '.py')
    mm_path = os.path.join(basepath, 'mm', name + '.mm')
    mmc_path = mm_path + 'c'

    click.echo(COMPILING + '%s.mm' %name)
    compile_mm(mm_path)

    # mm
    for bin in bins:
        print
        click.echo(BENCHING + os.path.basename(name) + ' (%s)' %os.path.basename(bin))

        bench_mm(mmc_path, n, bin)

    # pypy
    print
    click.echo(BENCHING + name + '(PyPy)')
    bench_pypy(py_path, n)

    if cpython:
        print
        click.echo(BENCHING + name + '(CPython)')
        bench_cpython(py_path, n)

@click.command()
@click.option('-n', default=1)
@click.option('--target', '-t', default='*')
@click.option('--cpython', default=False)
@click.argument('name')
def cli(name, n, target, cpython):
    binpath = os.path.normpath(os.path.join(basepath, '..', 'bin'))
    bins = []

    target_match = re.match(r'([\.0-9]+)\+', target)
    if target_match:
        target_ = map(int, target_match.groups()[0].split('.'))
        for path in glob.glob(os.path.join(binpath, 'rpin*')):
            match = re.match(r'rpin(\d+\.\d+\.\d+)', path.rsplit('/',1)[1])
            if match:
                other = map(int, match.groups(0)[0].split('.'))
                if target_ <= other:
                    bins.append(path)

    # elif target=='*' or re.match('r[\.0-9]+', target):
    #     bins = glob.glob(os.path.join(binpath, 'rpin.*'+target))


    if re.match(r'\d+', name):
        try:
            path = glob.glob(os.path.join(basepath, 'mm', name + '-*.mm'))[0]
            b_name = os.path.basename(path).rsplit('.', 1)[0]
            bench(b_name, n, bins, cpython=cpython)
        except IndexError:
            print 'No matching benchmark ' + name

if __name__ == '__main__':
    cli()