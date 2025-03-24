import uuid


def is_valid_numeric_id(id) -> bool:
    return isinstance(id, int) or (isinstance(id, str) and id.isdigit())


def is_valid_uuid(id, version=4) -> bool:
    try:
        uuid.UUID(str(id), version=version)
        return True
    except ValueError:
        return False
