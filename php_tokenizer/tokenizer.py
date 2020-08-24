#!/usr/bin/env python3

from typing import Any, Callable, Dict, Iterable, List, Optional, Union

from .common.base import T2, OP_handlers
from .common.vld import VLD, Func_block, Opa
from .utils.handlers import (builtin_handlers, known_ext_source,
                             known_filter_ops, known_filters,
                             known_web_sources)
from .utils.helper import PHP_Vars


class Op_core(OP_handlers):
    def __init__(self, t: T2):
        assert (isinstance(t, T2))
        self._bind = t
        self._handlers: Dict[str, Callable[[Opa, PHP_Vars, OP_handlers],
                                           Union[str, List[str]]]] = {}

    @property
    def bind(self) -> T2:
        return self._bind

    def add_handlers(self,
                     extra: Dict[str, Callable[[Opa, PHP_Vars, OP_handlers],
                                               Union[str, List[str]]]],
                     force=False):
        for k, v in extra.items():
            if force:
                self._handlers[k] = v
            elif not self._handlers.get(k, None):
                self._handlers[k] = v

    def call(self, opa: Opa, pvars: PHP_Vars) -> Union[str, List[str]]:
        h = self._handlers.get(opa.op)
        if h:
            return h(opa, pvars, self)
        else:
            return opa.op


class Tokenizer_v2(T2):
    def __init__(self, path: str):
        self.src_path = path
        self.tokens: List[str] = []
        funcs: List[Func_block] = VLD(path).func_blocks
        self.func_table: Dict[str, Func_block] = {}
        for func in funcs:
            self.func_table[self.calc_func_key(func.file_name,
                                               func.function_name,
                                               func.class_name)] = func
        self.entry = self.calc_func_key(path, None, None)
        self.bind = Op_core(self)
        self.bind.add_handlers(builtin_handlers)
        self.key_stack: List[str] = []
        self.sinks: List[str] = []
        self._shared_stack = []
        self._shared_queue = []
        self._shared_queue_ct = [0]
        self._ignore: List[str] = []

    @property
    def ignore(self) -> List[str]:
        return self._ignore

    @ignore.setter
    def ignore(self, v: Iterable):
        self._ignore = List(v)

    def _get_tokens(self, block: Func_block) -> List[str]:
        self.key_stack.append(
            self.calc_func_key(block.file_name, block.function_name,
                               block.class_name))
        op_set = set([opa.op for opa in block.op_arrays])
        op1_set = set([opa.op1 for opa in block.op_arrays])
        op2_set = set([opa.op2 for opa in block.op_arrays])
        is_src = True if not op1_set.isdisjoint(
            known_web_sources) or not op1_set.isdisjoint(
                known_ext_source) else False
        is_filter = True if not op2_set.isdisjoint(
            known_filters) or not op_set.isdisjoint(
                known_filter_ops) else False
        is_sink = True if 'ECHO' in op_set else False
        res = []
        pvars = PHP_Vars(block.vtags, block.compiled_vars, self._shared_stack,
                         self._shared_queue, self._shared_queue_ct)
        for opa in block.op_arrays:
            if opa.is_dead:
                continue
            tmp = self.bind.call(opa, pvars)
            if isinstance(tmp, list):
                if is_src or is_filter or is_sink:
                    res.extend(tmp)
                elif opa.op not in self.ignore:
                    tmp.pop(0)
                    res.extend(tmp)
                else:
                    res.extend(tmp)
            elif is_src or is_filter or is_sink:
                res.append(tmp)
        self.key_stack.pop()
        return res

    def get_tokens(self) -> List[str]:
        if self.entry not in self.func_table.keys():
            raise Exception('Entry not found')
        if not self.tokens:
            self.tokens = self._get_tokens(self.get_func_block(self.entry))
        return self.tokens

    @staticmethod
    def calc_func_key(file_name: Optional[str], func_name: Optional[str],
                      class_name: Optional[str]) -> str:
        return "{0}:{1}:{2}".format(file_name, func_name, class_name)

    def current_key(self) -> Optional[str]:
        if self.key_stack:
            return self.key_stack[-1]
        else:
            return None

    def get_func_block(self, key: str) -> Optional[Func_block]:
        return self.func_table.get(key)

    def add_handlers(self,
                     extra: Dict[str, Callable[[Opa, PHP_Vars, List[Any]],
                                               Union[str, List[str]]]],
                     force=False):
        self.bind.add_handlers(extra, force)
