def is_valid_numeric_id(id) -> bool:
    return isinstance(id, int) or (isinstance(id, str) and id.isdigit())
