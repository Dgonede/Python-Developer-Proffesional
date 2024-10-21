"""
TODO:

`return_self` should return an instance of the same type as the current enclosed class.
"""

#import typing


#class Foo:
#    def return_self(self):
#        ...


# solution
from typing import Self


class Foo:
    def return_self(self) -> Self:
        return self