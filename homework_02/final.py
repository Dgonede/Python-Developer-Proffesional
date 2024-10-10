"""
TODO:

Make sure `my_list` cannot be re-assigned to.
"""

from typing import Final, List


my_list: Final[List[int]] = []

my_list.append(1)
my_list = [] # expect-type-error
my_list = "something else" # expect-type-error




