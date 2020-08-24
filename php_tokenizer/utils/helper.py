#!/usr/bin/env python3

from typing import Any, Dict, List


class PHP_Vars(object):
    def __init__(self, vtags: List[int], cvs: List[str],
                 shared_stack: List[Any], shared_queue: List[Any], shared_queue_ct: List[int]):
        self._vtags = vtags
        self._cvs: Dict[str, str] = {}
        for i, cv in enumerate(cvs):
            self._cvs['!{}'.format(i)] = "$" + cv
        self._vars_map: Dict[int, Any] = {}
        for tag in self._vtags:
            self._vars_map[tag] = {}
        self._stack = shared_stack
        self._queue = []
        assert(shared_queue_ct)
        self._queue_ct: List[int] = shared_queue_ct

    def get(self, key: str, op_no: int, default=None) -> Any:
        assert (self._vtags and 0 <= op_no < len(self._vtags))
        check_list = self._vtags[:op_no + 1]
        tag = check_list.pop()
        v = self._vars_map[tag].get(key)
        if v:
            return v
        check_list.reverse()
        for ctag in check_list:
            if ctag < tag or (ctag & tag) == 0:
                continue
            v = self._vars_map[ctag].get(key)
            if v:
                return v
        v = self._cvs.get(key, default)
        return v

    def set(self, key: str, v: Any, op_no: int):
        assert (self._vtags and 0 <= op_no < len(self._vtags))
        self._vars_map[self._vtags[op_no]][key] = v

    def append(self, v):
        self._stack.append(v)

    def pop(self) -> Any:
        return self._stack.pop() if self._stack else None

    def new_qct(self):
        self._queue_ct.append(0)

    def del_qct(self):
        assert(self._queue_ct and self._queue_ct[-1] >= len(self._queue))
        for i in range(self._queue_ct[-1]):
            self.recv()
        self._queue_ct.pop()

    def send(self, v):
        self._queue.append(v)
        self._queue_ct[-1] += 1

    def recv(self, default=None) -> Any:
        if self._queue_ct[-1] <= 0:
            return default
        res = self._queue.pop(0)
        self._queue_ct[-1] -= 1
        return res


class Vars_obj(object):
    def __init__(self, vars_tags: List[int], cvs: List[str]):
        self.vars_tags = vars_tags
        self.cvs = {}
        self.vars_map = {}
        for i, cv in enumerate(cvs):
            self.cvs["!{}".format(i)] = "$" + cv
        for tag in self.vars_tags:
            self.vars_map[tag] = {}

    def get(self, key: str, n: int) -> Any:
        assert (self.vars_tags and 0 <= n < len(self.vars_tags))
        check_list = self.vars_tags[:n + 1]
        tag = check_list.pop()
        res = self.vars_map[tag].get(key, None)
        if res:
            return res
        check_list.reverse()
        for ctag in check_list:
            if ctag <= tag or (ctag & tag) == 0:
                continue
            res = self.vars_map[ctag].get(key, None)
            if res:
                return res
        res = self.cvs.get(key, None)
        if res:
            return res
        return None
