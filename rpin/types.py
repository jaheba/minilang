
from rpin.exceptions import Panic

from rpython.rlib import rerased
from rpython.rlib.objectmodel import import_from_mixin


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

    def add__integer(self, other):
        raise Panic('Can not add %s to Integer' %self.__class__.__name__)

    def sub__integer(self, other):
        raise Panic('Can not subtract %s from Integer' %self.__class__.__name__)

    def mul__integer(self, other):
        raise Panic('Can not multiply %s by Integer' %self.__class__.__name__)

    def div__integer(self, other):
        raise Panic('Can not divide %s by Integer' %self.__class__.__name__)

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
    def __init__(self):
        self.strategy = emptyListStrategy
        self.empty_list()

    def _check_bounds(self, w_index):
        assert isinstance(w_index, Integer)
        index = w_index.i_value
        if index >= self.length():
            raise IndexError('%s not <= %s' %(index, self.length()))
        return index

    def to_bool(self):
        return self.length() > 0

    def attribute(self, name):
        if name == 'length':
            return Integer(self.length())
        else:
            raise AttributeError('uknown attribute %s' %name)

    def getitem(self, w_index):
        index = self._check_bounds(w_index)
        return self.strategy.getitem(self, index)

    def setitem(self, w_index, w_object):
        index = self._check_bounds(w_index)
        self.strategy.setitem(self, index, w_object)

    def append(self, w_item):
        self.strategy.append(self, w_item)

    def length(self):
        return self.strategy.length(self)

    def to_str(self):
        return self.strategy.to_str(self)

    def empty_list(self):
        self.storage = self.strategy.empty_list(self)


class ListStrategy(object):
    def to_str(self, w_list):
        raise NotImplementedError

    def getitem(self, w_list, index):
        raise NotImplementedError

    def setitem(self, w_list, index, w_item):
        raise NotImplementedError

    def append(self, w_list, index):
        raise NotImplementedError

    def to_str(self, w_list):
        raise NotImplementedError

    def length(self, w_list):
        raise NotImplementedError

    def empty_list(self, w_list):
        raise NotImplementedError

    def length(self, w_list):
        raise NotImplementedError


class AbstractListStrategy(object):
    @staticmethod
    def unerase(storage):
        raise NotImplementedError("abstract base class")

    @staticmethod
    def erase(obj):
        raise NotImplementedError("abstract base class")

    def length(self, w_list):
        return len(self.unerase(w_list.storage))


class EmptyListStrategy(ListStrategy):
    import_from_mixin(AbstractListStrategy)

    erase, unerase = rerased.new_erasing_pair("empty")
    erase = staticmethod(erase)
    unerase = staticmethod(unerase)

    def append(self, w_list, w_item):
        if type(w_item) is Integer:
            w_list.strategy = integerListStrategy
        else:
            w_list.strategy = objectListStrategy

        w_list.empty_list()
        w_list.append(w_item)

    def to_str(self, w_list):
        return '[]'

    def empty_list(self, w_list):
        return self.erase([])


emptyListStrategy = EmptyListStrategy()


class ObjectListStrategy(ListStrategy):
    import_from_mixin(AbstractListStrategy)

    erase, unerase = rerased.new_erasing_pair("object")
    erase = staticmethod(erase)
    unerase = staticmethod(unerase)

    def append(self, w_list, w_item):
        self.unerase(w_list.storage).append(w_item)

    def to_str(self, w_list):
        return '[%s]' %(', '.join([item.to_str()
            for item in self.unerase(w_list.storage)]))

    def getitem(self, w_list, index):
        return self.unerase(w_list.storage)[index]

    def setitem(self, w_list, index, w_item):
        self.unerase(w_list.storage)[index] = w_item

    def empty_list(self, w_list):
        return self.erase([])


objectListStrategy = ObjectListStrategy()


class IntegerListStrategy(ListStrategy):
    import_from_mixin(AbstractListStrategy)

    erase, unerase = rerased.new_erasing_pair("integer")
    erase = staticmethod(erase)
    unerase = staticmethod(unerase)

    def append(self, w_list, w_item):
        if isinstance(w_item, Integer):
            self.unerase(w_list.storage).append(w_item.i_value)
        else:
            self.switch_to_object_strategy(w_list)
            w_list.append(w_item)

    def switch_to_object_strategy(self, w_list):
        storage = []

        for i in self.unerase(w_list.storage):
            storage.append(Integer(i))

        w_list.strategy = objectListStrategy
        w_list.storage = objectListStrategy.erase(storage)

    def to_str(self, w_list):
        return '[%s]' %(', '.join([str(x) for x in self.unerase(w_list.storage)]))

    def getitem(self, w_list, index):
        return Integer(self.unerase(w_list.storage)[index])

    def setitem(self, w_list, index, w_item):
        if type(w_item) is Integer:
            self.unerase(w_list.storage)[index] = w_item.i_value
        else:
            self.switch_to_object_strategy(w_list)
            w_list.strategy.setitem(w_list, index, w_item)

    def empty_list(self, w_list):
        return self.erase([])


integerListStrategy = IntegerListStrategy()


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
