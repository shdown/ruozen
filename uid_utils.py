# (c) 2026 shdown
# This code is licensed under MIT license (see LICENSE.MIT for details)

import random


def empty():
    return '#'


def gen_random():
    b = random.randbytes(16)
    return b.hex().upper()


def is_valid_uid(uid, accept_empty=False):
    if accept_empty and uid == '#':
        return True

    if len(uid) != 32:
        return False

    for c in uid:
        if not c in '0123456789ABCDEF':
            return False
    return True
