"""Helper functions module to support imports and keep lambda_handler clean."""


def ignore_space_and_case(s: str,
                          ignore_spaces: bool = True,
                          ignore_case: bool = True) -> str:
    """Transform the supplied string by ignoring spaces and/or changing to upper case."""
    if ignore_spaces:
        s = s.replace(" ", "")
    if ignore_case:
        s = s.upper()
    return s


def lists_equal(list_1: list, list_2: list) -> bool:
    """Compares two lists for element equality."""
    return len(list_1) == len(list_2) and sorted(list_1) == sorted(list_2)
