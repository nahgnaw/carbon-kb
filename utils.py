# -*- coding: utf8 -*-

import time
import functools


def timeit(func):
    @functools.wraps(func)
    def newfunc(*args, **kwargs):
        start_time = time.time()
        func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        print('Function [{}] finished in {} s'.format(
            func.__name__, int(elapsed_time)))
    return newfunc
