def clamp(value):
    if not isinstance(value, int):
        raise ValueError("not_int")
    return max(0, min(100, value))
