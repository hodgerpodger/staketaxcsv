import json
import os
from common.Cache import Cache
KOINLY_NULL_MAP_JSON = os.path.dirname(os.path.realpath(__file__)) + "/../_reports/koinly_null_map.json"


class NullMap:

    null_map = []
    cache = None

    @classmethod
    def _cache(cls):
        if not cls.cache:
            cls.cache = Cache()
        return cls.cache

    @classmethod
    def load(cls, use_cache=False):
        if use_cache:
            cls.null_map = cls._cache().get_koinly_null_map()
            if not cls.null_map:
                cls.null_map = []
        else:
            if os.path.exists(KOINLY_NULL_MAP_JSON):
                with open(KOINLY_NULL_MAP_JSON, 'r') as f:
                    cls.null_map = json.load(f)

    @classmethod
    def flush(cls, use_cache):
        if use_cache:
            cls._cache().set_koinly_null_map(cls.null_map)
        else:
            with open(KOINLY_NULL_MAP_JSON, 'w') as f:
                json.dump(cls.null_map, f, indent=4)

    @classmethod
    def get_null_symbol(cls, symbol):
        if symbol not in cls.null_map:
            cls.null_map.append(symbol)

        index = cls.null_map.index(symbol)

        # Koinly only accepts indices > 0
        return "NULL{}".format(index + 1)

    @classmethod
    def list_for_display(cls, use_cache=False):
        cls.load(use_cache)

        out = []
        for index in range(len(cls.null_map)):
            out.append(("NULL{}".format(index + 1), cls.null_map[index]))
        return out
