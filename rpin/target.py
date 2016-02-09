import os
from interpreter import Interpreter, Object, Integer, String, Code
from interpreter import op_codes, CONST_INT, JUMP, JNE, ARG_COUNT, CALL, RETURN, CREATE_LIST, CALL_METHOD, LOAD_LOCAL, STORE_LOCAL


def parse(text):
    program = []
    args = []

    for line in text.splitlines():
        inst, arg = line.split(' ', 1)

        op_code = op_codes[inst]
        program.append(op_code)

        if op_code in (CONST_INT, JUMP, JNE, ARG_COUNT, CALL, CALL_METHOD, RETURN, CREATE_LIST, LOAD_LOCAL, STORE_LOCAL):
            args.append(Integer(int(arg)))
        else:
            # program.append((op_code, String(arg)))
            args.append(String(arg))

    return Code(program[:], args[:])

# class NoneObject(Object):
#     pass

def run(fp):
    
    program_contents = ""
    while True:
        read = os.read(fp, 4096)
        if len(read) == 0:
            break
        program_contents += read
    os.close(fp)

    code = parse(program_contents)
    i = Interpreter(code)
    return i.run()
    # program, bm = parse(program_contents)
    # mainloop(program, bm)

    # for key, value in i.namespace.items():
        # print '%s = %s' %(key, value.i_value)

    # print i.namespace.get('z').i_value
    # print 'x = %s' % i.storage[0]
    # print 'N = %s' % i.storage[1]

def entry_point(argv):
    try:
        filename = argv[1]
    except IndexError:
        print "You must supply a filename"
        return 1

    run(os.open(filename, os.O_RDONLY, 0777))
    return 0

def target(*args):
    return entry_point, None

if __name__ == "__main__":
    import sys
    entry_point(sys.argv)