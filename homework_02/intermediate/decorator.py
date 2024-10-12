"""
TODO:

Define a decorator that wraps a function and returns a function with the same signature.
"""
# from typing import Callable, TypeVar


#def decorator(func):
#    return func

# solution 
from typing import Callable, TypeVar

num = TypeVar("num", bound=Callable)

def decorator(func: num) -> num:
    return func