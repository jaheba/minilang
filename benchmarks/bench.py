

import os.path
import subprocess

import re
import click
import glob

from minilang.translate import to_bytecode

basepath = os.path.dirname(os.path.abspath(__file__))
rel_basepath = os.path.dirname(__file__)

def compile_mm(path):

    with open(path+'c', 'w') as fobj:
        fobj.write(to_bytecode(path))

def multitime(cmd, n=1):
    pipe = subprocess.Popen(['multitime', '-n', str(n)] + cmd, stderr=subprocess.PIPE)
    stdout, stderr = pipe.communicate()
    for line in stderr.split('\n'):
        print '\t' + line

def bench_mm(target, n, bin):
    multitime([bin, os.path.abspath(target)], n=n)

def bench_pypy(target, n):
    multitime(['pypy', target], n=n)

def bench_cpython(target, n):
    multitime(['/usr/bin/python', target], n=n)


COMPILING = click.style('\tCompiling: ', fg='yellow')
BENCHING = click.style('\tBenchmarking: ', fg='cyan')
BENCHMARK = click.style('Benchmark: ', fg='red')

def bench(name, n=1, bins=None, cpython=False):
    py_path = os.path.join(basepath, 'py', name + '.py')
    mm_path = os.path.join(basepath, 'mm', name + '.mm')
    mmc_path = mm_path + 'c'

    click.echo(BENCHMARK + name)
    # click.echo(COMPILING + '%s.mm' %name)
    compile_mm(mm_path)

    # mm
    for bin in bins:
        click.echo(BENCHING + os.path.basename(bin))

        bench_mm(mmc_path, n, bin)

    # pypy
    click.echo(BENCHING + 'PyPy')
    bench_pypy(py_path, n)

    if cpython:
        click.echo(BENCHING + 'CPython')
        bench_cpython(py_path, n)

@click.command()
@click.option('-n', default=1)
@click.option('--target', '-t', default='*')
@click.option('--cpython/--no-cpython', default=False)
@click.argument('names', nargs=-1)
def cli(names, n, target, cpython):
    binpath = os.path.normpath(os.path.join(rel_basepath, '..', 'bin'))
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

    for name in names:
        if name == 'all':
            for path in glob.glob(os.path.join(basepath, 'mm', '*.mm')):
                b_name = os.path.basename(path).rsplit('.', 1)[0]
                bench(b_name, n, bins, cpython=cpython)
        
        elif re.match(r'\d+', name):
            try:
                path = glob.glob(os.path.join(basepath, 'mm', name + '-*.mm'))[0]
                b_name = os.path.basename(path).rsplit('.', 1)[0]
                bench(b_name, n, bins, cpython=cpython)
            except IndexError:
                print 'No matching benchmark ' + name

if __name__ == '__main__':
    cli()
