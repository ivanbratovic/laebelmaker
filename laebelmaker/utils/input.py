"""Module containing useful functions to get user input"""

from typing import Any, Optional
import readline

__author__ = "Ivan Bratović"
__copyright__ = "Copyright 2023, Ivan Bratović"
__license__ = "MIT"


def input_prefilled(prompt: str, text: str = "") -> str:
    """Wrapper for built-in input. Prefills user input using
    the readline module.

    Args:
        prompt (str): The prompt for the input function.
        text (str, optional): Text to prefill. Deafults to the empty string.
    Returns:
        The return value of the wrapped input.
    """

    def hook() -> None:
        readline.insert_text(text)
        readline.redisplay()

    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result


def input_item(name: str, typ: type, item_orig: Optional[Any] = None) -> Any:
    """Wrapper for input_prefilled. Generates a useful prompt and
    prefill text, based on the type of the item given, and its value.

    Arguments:
        name (str): The item's name, for the prompt text.
        typ (type): The item's exact type, as a <class 'type'> object.
        item_orig: The original value of the item, for prefilling.
    Returns:
        The inputted item, converted to its original type.
    """
    if typ == int:
        hint_text = " (integer)"
    elif typ == bool:
        hint_text = " (yes/No)"
    else:
        hint_text = ""
    new_value: str = input_prefilled(
        f"Enter value for {name.replace('_', ' ')!r}{hint_text}: ",
        str(item_orig) if item_orig else "",
    )
    if typ == bool:
        if new_value.lower() not in ("true", "yes", "1", "y"):
            new_value = ""
    return typ(new_value if new_value else False)


def query_selection(options: list[Any], item_name: str, default_index: int = 0) -> Any:
    """Asks the user to select a single value from a list of possible
    values, by index. If only a single item is given, returns it.

    Arguments:
        options (list): List of items to choose from.
        item_name (str): The name of the item, for the prompt text.
        default_index (int, optional): The index chosen when user does not input
            an exact index. Defaults to 0.
    Returns:
        The item selected by the user from the list of options.
    """
    if not options:
        raise ValueError("Options list must not be empty for query_selection.")
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
    """Wrapper for input_item. Generates the type automatically from
    the given item value.

    Arguments:
        item_orig: The original value of the item.
        item_name (str): The name of the item, for the prompt text.
    Returns:
        The new value of the item, i.e. the input converted to the item's type.
    """
    typ: type = type(item_orig)
    return input_item(item_name, typ, item_orig)
