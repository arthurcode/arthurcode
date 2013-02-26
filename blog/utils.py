def is_blank(value):
    """
    Returns true if `value` is None, the empty string, or a string composed solely of whitespace.
    This method can handle both regular strings and unicode strings.
    """
    if not value:
        return True
    return isinstance(value, (str, unicode)) and not value.strip()
