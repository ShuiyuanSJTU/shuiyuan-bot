from functools import wraps

def Singleton(cls):
    cls._instance = None
    cls._origin_new = cls.__new__
    cls._origin_init = cls.__init__
    @wraps(cls.__new__)
    def _singleton_new(cls, *args, **kwargs):
        if cls._instance is None:
            sin_instance = cls._origin_new(cls)
            sin_instance._origin_init(*args, **kwargs)
            cls._instance = sin_instance
        # skip original __init__
        cls.__init__ = _singleton_init
        return cls._instance
    @wraps(cls.__init__)
    def _singleton_init(self, *args, **kwargs):
        # restore original __init__
        self.__class__.__init__ = cls._origin_init
    cls.__new__ = staticmethod(_singleton_new)
    return cls