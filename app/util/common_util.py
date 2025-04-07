import json


def strtobool(val):
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    if isinstance(val, bool):
        return val

    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        raise ValueError("invalid truth value %r" % (val,))


def get_key_from_dict(dictionary, value):
    return next((key for key, val in dictionary.items() if val == value), None)


def try_loads(json_str):
    try:
        json_str = json.loads(json_str)
    except Exception:
        json_str = None

    return json_str


def try_dumps(target):
    try:
        result = json.dumps(target)
    except Exception:
        result = None

    return result
    