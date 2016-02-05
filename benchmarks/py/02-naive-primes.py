
primes = []
candidate = 2

while candidate <= 100000:
    i = 2
    is_prime = True
    while i < candidate//2+1:
        if candidate%i == 0:
            is_prime = False
            break
        i = i + 1

    if is_prime:
        primes.append(candidate)

    candidate = candidate + 1;