"""
TODO:

foo should accept an integer argument.
"""


def foo(x: int) -> None:
    pass


foo(10)
foo("10") # expect-type-error
