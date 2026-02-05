# (c) 2026 shdown
# This code is licensed under MIT license (see LICENSE.MIT for details)

import re


_db = []


def command_decorator(regex_str):
    regex = re.compile(regex_str, flags=re.I)

    def decorator(func):
        _db.append((regex, func))
        return func

    return decorator


def find_and_exec_command(text):
    for regex, func in _db:
        m = regex.fullmatch(text)
        if m is not None:
            result = func(m)
            return True, result
    return False, None
