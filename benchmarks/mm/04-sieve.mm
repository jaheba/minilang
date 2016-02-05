
fn primes_sieve2 limit{
    primes := [];
    i := 0;
    a := [];

    while i < limit {
        a::append(true);
        i := i + 1;
    }
    a[0 := false];
    a[1 := false];

    i := 0;
    while i < limit{
        is_prime := a[i];
        if is_prime{
            primes::append(i);
            
            j := 0;
            while j < limit{
                a[j := false];
                j := j + i;
            }
        }
        i := i + 1;
    }
    ^ primes;
}

primes_sieve2(3000000);
