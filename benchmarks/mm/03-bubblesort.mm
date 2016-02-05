
fn bubblesort list {
    boundry := list::length -1;

    while boundry > 0 {
        cur := 0;
        while cur < boundry {
            if list[cur] > list[boundry] {
                list[cur <:> boundry];
            }
            cur := cur + 1;
        }
        boundry := boundry - 1;
    }
    ^ list;
}

list := [];

i := 20000;
while i > 0 {
    list::append(i);
    i := i - 1;
}

bubblesort(list);
