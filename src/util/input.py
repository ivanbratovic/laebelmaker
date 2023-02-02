"""Module containing useful functions to get user input"""

from typing import *
from util.errors import NoInformationException
import readline

__author__ = "Ivan Bratović"
__copyright__ = "Copyright 2022, Ivan Bratović"
__license__ = "MIT"


def input_prefilled(prompt: str, text: str) -> str:
    def hook() -> None:
        readline.insert_text(text)
        readline.redisplay()

    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result


def input_item(name: str, typ: type) -> Any:
    if typ == int:
        hint_text = " (integer)"
    elif typ == bool:
        hint_text = " (yes/No)"
    else:
        hint_text = ""
    new_value: str = input(f"Enter value for {name.replace('_', ' ')!r}{hint_text}: ")
    if typ == bool:
        if new_value.lower() not in ("true", "yes", "1", "y"):
            new_value = ""
    return typ(new_value)


def query_selection(options: list[Any], item_name: str, default_index: int = 0) -> Any:
    if len(options) == 0:
        raise NoInformationException(f"No {item_name} choices given.")
    if len(options) == 1:
        return options[0]
    print(f"Found multiple {item_name}s.")
    for i, service in enumerate(options):
        print(f" {i+1}. {service}")
    answer: str = input(
        f"{item_name.capitalize()} number to use (default {default_index + 1}): "
    )
    selection: int = default_index
    if answer:
        selection = int(answer) - 1
    assert selection in range(len(options)), "Selected index out of range"
    return options[selection]


def query_change(item_orig: Any, item_name: str) -> Any:
    typ: type = type(item_orig)
    answer = input_prefilled(f"Enter new value for '{item_name}': ", item_orig)
    if answer:
        return typ(answer)
    return typ(item_orig)
