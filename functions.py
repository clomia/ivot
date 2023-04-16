def gen():
    for i in range(10):
        if i == 5:
            break
        else:
            yield i


it = gen()

itit = enumerate(it)


print(next(itit))
print(next(itit))
print(next(itit))
print(next(itit))
