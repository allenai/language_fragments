from collections import defaultdict,OrderedDict
from typing import Dict, TypeVar, Generic, Optional
from language_fragments.base import UtilityClass

class CacheUtility(UtilityClass):
    """Base class for cachers"""
    def __getitem__(self,key):
        raise NotImplementedError
    def __setitem__(self,K,V):
        raise NotImplementedError

class LRUCache(CacheUtility):
    """LRU cache utility, taken from AI2 lm-explorer. 
    :see also: https://www.kunxi.org/2014/05/lru-cache-in-python/
    """
    def __init__(self, capacity, default_value=None):
        self._capacity = capacity
        self._cache =  OrderedDict()
        self._default_value = default_value

    def __getitem__(self, key):
        if self._capacity == 0:
            return self._default_value
        try:
            value = self._cache.pop(key)
            self._cache[key] = value
            return value
        except KeyError:
            return self._default_value

    def __setitem__(self, K, V):
        if self._capacity == 0:
            return

        try:
            self._cache.pop(K)
        except KeyError:
            if len(self._cache) >= self._capacity:
                self._cache.popitem(last=False)
        self._cache[K] = V
