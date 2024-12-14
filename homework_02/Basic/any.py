"""
TODO:

Modify `foo` so it takes an argument of arbitrary type.
"""
def check_args(func):
    def wrapper(*args):
        if len(args) != 1:
            print(f"except {args} - вызвано с неправильным количеством аргументов")
        else:
            return func(*args)
    return wrapper
@check_args
def foo(any):
    pass

    """⬆️ Change me. No need to implement the function."""  
foo(1)
foo("10")
foo(1, 2) # expect-type-error






