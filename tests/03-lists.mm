
a = [];
assert a::length == 0;

a.append(42);
assert a::length == 1;
assert a[0] == 42;