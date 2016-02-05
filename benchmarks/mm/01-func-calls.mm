

fn cubic n {
    ^ square(n) * n;
}

fn square n {
    ^ n*n;
}

sum := 0;
MILLION := 1000000;

i := 0;
while i < 10*MILLION {
    sum := sum + i + square(i) + cubic(i);
    i := i + 1;
}
