
a := 42;
b := a;

assert a == a;
assert a == b;
assert b == a;

assert a == 42;
assert 42 == a;

assert b == 42;
assert 42 == b;