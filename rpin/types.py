
from rpin.exceptions import Panic

class Object(object):
    __slots__ = ()
    def to_str(self):
        return '<Empty Object>'

    for name, op in ('add', '+'), ('sub', '-'), ('mul', '*'), ('div', '/'):
        exec '''def {name}(self, other):
        raise Panic('Operation {op} not defined for %s'
            %self.__class__.__name__)'''.format(name=name, op=op)
    


        for type_ in 'integer', 'string', 'list', 'bool':
            exec '''def {name}__{type}(self, other):
        raise Panic('Can find operation {op} %s for and {type}'
            %self.__class__.__name__)'''.format(name=name, op=op, type=type_)



    # def add__integer(self, other):
    #     raise Panic('Can not add %s to Integer' %self.__class__.__name__)

    # def sub__integer(self, other):
    #     raise Panic('Can not subtract %s from Integer' %self.__class__.__name__)

    # def mul__integer(self, other):
    #     raise Panic('Can not multiply %s by Integer' %self.__class__.__name__)

    # def div__integer(self, other):
    #     raise Panic('Can not divide %s by Integer' %self.__class__.__name__)


    def eq(self, other):
        raise Panic('Comparison == not defined for %s' %self.__class__.__name__)

    def ne(self, other):
        raise Panic('Comparison != not defined for %s' %self.__class__.__name__)

    def lt(self, other):
        raise Panic('Comparison < not defined for %s' %self.__class__.__name__)

    def le(self, other):
        raise Panic('Comparison <= not defined for %s' %self.__class__.__name__)

    def gt(self, other):
        raise Panic('Comparison > not defined for %s' %self.__class__.__name__)

    def ge(self, other):
        raise Panic('Comparison >= not defined for %s' %self.__class__.__name__)


class Integer(Object):
    _immutable_fields_ = "i_value",

    def __init__(self, value):
        self.i_value = value

    def to_str(self):
        return str(self.i_value)

    def to_bool(self):
        return self.i_value != 0

    for name, op in (('eq', '=='), ('ne', '!='), ('lt', '<'), ('le', '<'),
                     ('gt', '>='), ('ge', '>=')):
        exec '''def {name}(self, other):
            return other.l{name}__integer(self.i_value)'''.format(name=name)

        exec '''def l{name}__integer(self, i_value):
            if i_value {op} self.i_value:
                return w_True
            else:
                return w_False'''.format(name=name, op=op)

    # calc
    for name, op in ('add', '+'), ('sub', '-'), ('mul', '*'), ('div', '//'):
        exec '''def {name}(self, other):
            return other.l{name}__integer(self.i_value)'''.format(name=name)
        
        exec '''def l{name}__integer(self, i_value):
            return Integer(i_value {op} self.i_value)'''.format(name=name, op=op)



class String(Object):
    _immutable_fields_ = "s_value",

    def __init__(self, value):
        self.s_value = value

    def to_str(self):
        return self.s_value

    def to_bool(self):
        return len(self.s_value)

    def add(self, other):
        return other.ladd__string(self.s_value)

    def ladd__string(self, other):
        return String(other + self.s_value)

class List(Object):
    def __init__(self, list):
        self.list = list

    def _check_bounds(self, w_index):
        assert isinstance(w_index, Integer)
        index = w_index.i_value
        if index  >= len(self.list):
            raise IndexError('%s not <= %s' %(index, len(self.list)))
        return index

    def getitem(self, w_index):
        index = self._check_bounds(w_index)
        return self.list[index]

    def setitem(self, w_index, w_object):
        index = self._check_bounds(w_index)
        self.list[index] = w_object

    def to_str(self):
        return '[%s]' %(', '.join([item.to_str() for item in self.list]))

    def to_bool(self):
        return len(self.list)

    def attribute(self, name):
        if name == 'length':
            return Integer(len(self.list))
        else:
            raise AttributeError('uknown attribute %s' %name)


class Bool(Object):
    _immutable_fields_ = "bool",

    def __init__(self, bool):
        self.bool = bool

    def to_bool(self):
        return self.bool

    def to_str(self):
        if self.bool:
            return 'True'
        else:
            return 'False'

w_True = Bool(True)
w_False = Bool(False)


class Function(Object):
    def __init__(self, address, arguments, namespace):
        self.address = address
        self.arguments = arguments
        self.namespace = namespace

    def to_str(self):
        return '<fn at %s>' %self.address