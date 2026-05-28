# -*- coding: utf-8 -*-
"""
Created on Thu May 28 10:05:41 2026

@author: trent
"""
from functools import wraps
from inspect import getfullargspec
from typing import Iterable, Self


class HybridMethod:
    """
    Wrapper method for making a method that can be used both as a class/static
    method with passed arguments or as a method that looks to the instance for
    the selected argument names.

    """

    def __init__(self, *check_kwargs: Iterable[str]) -> Self:
        self.check_kwargs = check_kwargs
        self.fn = None
        self.argspec = None

    def __call__(self, fn: callable) -> Self:
        self.fn = fn
        self.argspec = getfullargspec(self.fn)
        return self

    def __get__(self, instance: object, owner: type):
        if instance is None:

            @wraps(self.fn)
            def class_method(*args, **kwargs):
                return self.fn(owner, *args, **kwargs)
            return class_method

        @wraps(self.fn)
        def method(*args, **kwargs):
            # Override instance with passed args
            out_kwargs = {name: getattr(instance, name, None)
                          for name in self.check_kwargs
                          if getattr(instance, name, None)}
            arg_spec = dict(zip(self.argspec.args[1:], args[1:]))
            out_kwargs.update(arg_spec)
            out_kwargs.update(kwargs)
            return self.fn(instance, **out_kwargs)

        return method
