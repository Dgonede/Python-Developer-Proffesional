"""
TODO:

foo should accept a dict argument, both keys and values are string.
"""
from typing import Dict

def foo(x: Dict[str, str]):
    pass

args_list = [
    {"foo": "bar"},  
    {"foo": 1}       #except
]

for arg in args_list:
    if not isinstance(arg, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in arg.items()):
        print(f"except {arg} - аргумент должен быть Dict[str, str]")
    else:
        foo(arg)
