def test():
    if True:
        return
    try:
        pass
    except NonExistentName:
        pass

test()
print("Passed")
