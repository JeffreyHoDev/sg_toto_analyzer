import time
import functools

def process_time(fn):
    """
        Decorator for showing processing time
    """
    @functools.wraps(fn)
    def fn_wrapper(*args, **kwargs):
        t1 = time.time()
        fn(*args, **kwargs)
        t2 = time.time()
        print(f"Processed time:{t2 - t1}s")
    
    return fn_wrapper