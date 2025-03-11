a = iter([1, 2, 3, 4, 5])

count = 0
while True:
    try:
        for el in a:
            input()
            count += 1
            print(el)
            if count == 2:
                raise Exception('exception is now!')
        break
    except Exception as e:
        print('aue')
        # break