"""
TODO:

foo only accepts literal 'left' and 'right' as its argument.
"""


#def foo(direction):
#    ...


# solution
from typing import Literal

def foo(direction: Literal["left", "right"]):
    ...