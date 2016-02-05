
from rpython.rlib import jit

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

    @jit.purefunction
    def getindex(self, name):
        return self.attribute_indexes.get(name, -1)

    @jit.purefunction
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
        map = jit.hint(self.map, promote=True)
        index = map.getindex(jit.hint(name, promote_string=True))

        if index == -1:
            if self.parent is None:
                raise KeyError('Unknown variable %s' %name)
            else:
                return self.parent.get(name)

        return self.storage[index]

    def set(self, name, value):
        map = jit.hint(self.map, promote=True)
        index = map.getindex(jit.hint(name, promote_string=True))
        if index != -1:
            self.storage[index] = value
            return

        self.map = map.new_map_with_additional_attribute(name)
        self.storage.append(value)

