

def cubic(n):
    return square(n) * n


def square(n):
    return n*n


sum = 0
MILLION = 10**6

i = 0
while i < 10*MILLION:
    sum = sum + i + square(i) + cubic(i)
    i = i + 1