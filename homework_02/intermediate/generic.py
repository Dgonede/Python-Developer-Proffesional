"""
TODO:

The function `add` accepts two arguments and returns a value, they all have the same type.
"""


#def add(a, b):
#    ...


# solution
from typing import TypeVar

num = TypeVar("num")

def add(a:num, b:num) -> num:
    return add(a,b)
    