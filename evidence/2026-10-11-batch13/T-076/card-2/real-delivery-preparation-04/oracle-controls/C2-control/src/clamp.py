def clamp(value):
    if type(value) is not int:
        raise ValueError("not_int")
    return max(0, min(100, value))
