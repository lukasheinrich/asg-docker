# @author: Sebastien Binet <binet@cern.ch>
# @date:   March 2008
# @purpose: a set of decorators. Most of them (if not all) have been stolen
#           from here:
#           http://www.phyast.pitt.edu/~micheles/python/documentation.html
#
from __future__ import with_statement

__version__ = "$Revision$"
__author__  = "Sebastien Binet <binet@cern.ch>"

__all__ = [
    'memoize',
    'forking',
    'async',
    ]

import sys
import os
import itertools
from decorator import *

@decorator
def memoize(func, *args):
    """This decorator implements the memoize pattern, i.e. it caches the result
    of a function in a dictionary, so that the next time the function is called
    with the same input parameters the result is retrieved from the cache and
    not recomputed.
    """
    try:
        mem_dict = getattr(func, "_mem_dict")
    except AttributeError:
        # look-up failed so we have to build the cache holder
        mem_dict = {}
        setattr(func, "_mem_dict", mem_dict)
    try:
        return mem_dict[args]
    except KeyError:
        # look-up failed so we have to build the result the first time around
        # then we cache
        mem_dict[args] = result = func(*args)
        return result

# FIXME: does not work... func is an instance of FunctionMaker which cannot
#        be pickled...
import __builtin__
@decorator
def mp_forking(func, *args, **kwargs):
    import multiprocessing as mp
    ## pool = mp.Pool (processes=1)
    ## return pool.apply (func, *args, **kwargs)

    # create a local queue to fetch the results back
    def wrapping(func):
        q = mp.Queue()
        def wrap_fct(*args, **kwargs):
            try:
                res = func(*args, **kwargs)
            # catch *everything* and 're-raise'
            except BaseException,err:
                #import traceback; traceback.print_exc()
                res = err
            q.put(res)
        wrap_fct.q = q
        return wrap_fct

    func = wrapping(func)
    proc = mp.Process(target=func, args=args, kwargs=kwargs)
    proc.start()
    res = func.q.get()
    proc.join()
    proc.terminate()
    if isinstance(res, BaseException):
        #import traceback; traceback.print_exc()
        raise res
        #reraise_exception(exc,exc_info)
    return res

def reraise_exception(new_exc, exc_info=None):
    if exc_info is None:
        exc_info = sys.exc_info()
    _exc_class, _exc, tb = exc_info
    raise new_exc.__class__, new_exc, tb
    
@decorator
def forking(func, *args, **kwargs):
    """
    This decorator implements the forking patterns, i.e. it runs the function
    in a forked process.
    see:
     http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/511474
    """
    import os
    try:
        import cPickle as pickle
    except ImportError:
        import pickle
        
    # create a pipe which will be shared between parent and child
    pread, pwrite = os.pipe()

    # do fork
    pid = os.fork()

    ## parent ##
    if pid > 0:
        os.close(pwrite)
        with os.fdopen(pread, 'rb') as f:
            status, result = pickle.load(f)
        os.waitpid(pid, 0)
        if status == 0:
            return result
        else:
            remote_exc = result[0]
            reraise_exception(remote_exc)
            
    ## child ##
    else:
        os.close(pread)
        try:
            result = func(*args, **kwargs)
            status = 0
        except (Exception, KeyboardInterrupt), exc:
            import traceback
            exc_string = traceback.format_exc(limit=10)
            for l in exc_string.splitlines():
                print "[%d]"%os.getpid(),l.rstrip()
            result = exc, exc_string
            status = 1
        with os.fdopen(pwrite, 'wb') as f:
            try:
                pickle.dump((status,result), f, pickle.HIGHEST_PROTOCOL)
            except pickle.PicklingError, exc:
                pickle.dump((2,exc), f, pickle.HIGHEST_PROTOCOL)
        os._exit(0)
    pass # forking

            
### a decorator converting blocking functions into asynchronous functions
#   stolen from http://pypi.python.org/pypi/decorator/3.0.0
def _async_on_success(result): # default implementation
    "Called on the result of the function"
    return result

def _async_on_failure(exc_info): # default implementation
    "Called if the function fails"
    _exc_class, _exc, tb = exc_info
    raise _exc_class, _exc, tb
    pass

def _async_on_closing(): # default implementation
    "Called at the end, both in case of success and failure"
    pass

class Async(object):
    """
    A decorator converting blocking functions into asynchronous
    functions, by using threads or processes. Examples:

    async_with_threads =  Async(threading.Thread)
    async_with_processes =  Async(multiprocessing.Process)
    """

    def __init__(self, threadfactory):
        self.threadfactory = threadfactory

    def __call__(self, func,
                 on_success=_async_on_success,
                 on_failure=_async_on_failure,
                 on_closing=_async_on_closing):
        # every decorated function has its own independent thread counter
        func.counter = itertools.count(1)
        func.on_success = on_success
        func.on_failure = on_failure
        func.on_closing = on_closing
        return decorator(self.call, func)

    def call(self, func, *args, **kw):
        def func_wrapper():
            try:
                result = func(*args, **kw)
            except:
                func.on_failure(sys.exc_info())
            else:
                return func.on_success(result)
            finally:
                func.on_closing()
        name = '%s-%s' % (func.__name__, func.counter.next())
        thread = self.threadfactory(None, func_wrapper, name)
        thread.start()
        return thread

# default async decorator: using processes
def async(async_type='mp'):
    if async_type in ("mp", "multiprocessing"):
        from multiprocessing import Process
        factory = Process
    elif async_type in ("th", "threading"):
        from threading import Thread
        factory = Thread
    else:
        raise ValueError ("async_type must be either 'multiprocessing' "
                          "or 'threading' (got: %s)"%async_type)
    async_obj = Async (factory)
    return async_obj
        
    
