import json
import logging
import os
from common.Cache import Cache
KOINLY_NULL_MAP_JSON = os.path.dirname(os.path.realpath(__file__)) + "/../_reports/koinly_null_map.json"


class NullMap:

    def __init__(self, json_path=None):
        self.null_map = []
        self.cache = None
        self.json_path = json_path if json_path else KOINLY_NULL_MAP_JSON
        logging.debug("Using Koinly NullMap json file %s", self.json_path)

    def _cache(self):
        if not self.cache:
            self.cache = Cache()
        return self.cache

    def clear(self):
        if os.path.exists(self.json_path):
            os.remove(self.json_path)

    def load(self, use_cache=False):
        if use_cache:
            self.null_map = self._cache().get_koinly_null_map()
            if not self.null_map:
                self.null_map = []
        else:
            if self.json_path and os.path.exists(self.json_path):
                with open(self.json_path, 'r') as f:
                    self.null_map = json.load(f)

    def flush(self, use_cache):
        if use_cache:
            self._cache().set_koinly_null_map(self.null_map)
        else:
            if self.json_path:
                with open(self.json_path, 'w') as f:
                    json.dump(self.null_map, f, indent=4)

    def get_null_symbol(self, symbol):
        if symbol not in self.null_map:
            self.null_map.append(symbol)

        index = self.null_map.index(symbol)

        # Koinly only accepts indices > 0
        return "NULL{}".format(index + 1)

    def list_for_display(self, use_cache=False):
        self.load(use_cache)

        out = []
        for index in range(len(self.null_map)):
            out.append(("NULL{}".format(index + 1), self.null_map[index]))
        return out
