
from rpython.rlib import jit

from rpin.types import Object, Integer

class Cell(Object):
    def __init__(self, c_value):
        self.c_value = c_value

class IntCell(Object):
    def __init__(self, int_value):
        self.int_value = int_value

class Map(object):
    __slots__ = 'attribute_indexes', 'other_maps'
    _immutable_fields_ = 'attribute_indexes', 'other_maps'

    def __init__(self, inherited_attributes=None):
        self.attribute_indexes = {}
        self.other_maps = {}

        if inherited_attributes is not None:
            self.attribute_indexes.update(inherited_attributes)

    def _add_key(self, name):
        self.attribute_indexes[name] = len(self.attribute_indexes)

    @jit.elidable
    def getindex(self, name):
        return self.attribute_indexes.get(name, -1)

    @jit.elidable
    def new_map_with_additional_attribute(self, name):
        if self.getindex(name) != -1:
            return self

        if name not in self.other_maps:
            newmap = Map(self.attribute_indexes)
            newmap._add_key(name)
            self.other_maps[name] = newmap
        return self.other_maps[name]

EMPTY_MAP = Map()


class Namespace(object):

    def __init__(self, parent=None):
        self.map = EMPTY_MAP
        self.storage = []
        self.parent = parent

    def get(self, name):
        map = jit.promote(self.map)
        index = map.getindex(jit.hint(name, promote_string=True))

        if index == -1:
            if self.parent is None:
                raise KeyError('Unknown variable %s' %name)
            else:
                return self.parent.get(name)

        return self.storage[index]

    def set(self, name, value):
        map = jit.promote(self.map)
        index = map.getindex(jit.hint(name, promote_string=True))
        if index != -1:
            self.storage[index] = value
            return

        self.map = map.new_map_with_additional_attribute(name)
        self.storage.append(value)

class VersionTag(object):
    pass

class Namespace(object):
    _immutable_fields_ = ['version?']

    def __init__(self):
        self.dict = {}
        self.version = VersionTag()
    
    def get(self, name):
        jit.promote(self)
        version = self.version
        jit.promote(version)
        value = self._get(name, version)
        if value is None:
            raise KeyError

        if isinstance(value, Cell):
            return value.c_value
        elif isinstance(value, IntCell):
            return Integer(value.int_value)
        else:
            return value

    @jit.elidable
    def _get(self, name, version):
        assert version is self.version
        return self.dict.get(name, None)

    def set(self, name, value):
        old_value = self._get(name, self.version)

        if old_value is None:
            self.version = VersionTag()
            self.dict[name] = value
        elif isinstance(old_value, IntCell) and isinstance(value, Integer):
            old_value.int_value = value.i_value
        elif isinstance(old_value, Cell):
            old_value.c_value = value
        else:
            if isinstance(value, Integer):
                self.dict[name] = IntCell(value.i_value)
            else:
                self.dict[name] = Cell(value)
            self.version = VersionTag()
