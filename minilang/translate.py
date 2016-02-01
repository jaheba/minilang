


from minilang import compile


def to_bytecode(path):
    with open(path) as fobj:
        text = fobj.read()

    return '\n'.join('%s %s' %(inst) for inst in compile(text))


if __name__ == '__main__':
    import sys

    print to_bytecode(sys.argv[1])