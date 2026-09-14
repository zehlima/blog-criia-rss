"""Serialize native HTML parsing while keeping HTTP and object writes concurrent.

Containment for the observed native allocator abort in the extraction stage.
This does not claim that every native-parser defect is eliminated.
"""
from functools import wraps
from threading import RLock

_native_parser_lock = RLock()


def serialized_parser(fn):
    @wraps(fn)
    def guarded(*args, **kwargs):
        with _native_parser_lock:
            return fn(*args, **kwargs)
    return guarded
