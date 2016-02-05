
def primes_sieve2(limit):
    primes = []

    i = 0
    a = []
    while i < limit:
        a.append(True)
        i = i + 1

    a[0] = False
    a[1] = False

    i = 0
    while i < limit:
        is_prime = a[i]
        if is_prime:
            primes.append(i)
            
            j = 0
            while j < limit:
                a[j] = False
                j = j + i

        i = i + 1
    return primes

primes_sieve2(3000000)
