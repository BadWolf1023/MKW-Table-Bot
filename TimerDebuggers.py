from time import time
import functools

DEBUGGING = True

def timer_coroutine(func):
    # This function shows the execution time of 
    # the function object passed
    if not DEBUGGING:
        return func
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        t1 = time()
        result = await func(*args, **kwargs)
        t2 = time()
        print(f'Function {func.__name__!r} executed in {(t2-t1):.4f}s')
        return result
    return wrapper

def timer(func):
    # This function shows the execution time of 
    # the function object passed
    if not DEBUGGING:
        return func
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        print(f'Function {func.__name__!r} executed in {(t2-t1):.4f}s')
        return result
    return wrapper
  