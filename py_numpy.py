import numpy as np


class InvalidValueError(Exception):
    pass


class DivideByZeroError(Exception):
    pass


class UnderflowError(Exception):
    pass


def err_handler(err, flag):
    # 1 << 0: divide by zero
    # 1 << 1: overflow
    # 1 << 2: underflow
    # 1 << 3: invalid value
    error_list = (0, DivideByZeroError, OverflowError, 0,
                  UnderflowError, 0, 0, 0, InvalidValueError)
    raise error_list[flag](err)

np.seterrcall(err_handler)
np.seterr(all='call')

try:
    np.float64(1.0) / np.float64(0.0)
except DivideByZeroError:
    # TODO
    pass

try:
    np.float64(0.0) / np.float64(0.0)
except InvalidValueError:
    # TODO
    pass

try:
    np.exp(-1000)
except UnderflowError:
    # TODO
    pass


try:
    np.int16(32000) * np.int16(3)
except UnderflowError:
    # TODO
    pass

np.seterr(all='raise')

try:
    # expression
except FloatingPointError as e:
    if e.startswith('invalid'):
        # TODO
        pass
    elif e.startswith('over'):
        # TODO
        pass
    elif e.startswith('under'):
        # TODO
        pass
    else: # e.startswith('divide')
        # TODO
        pass