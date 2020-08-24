#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Union

from ..utils.helper import PHP_Vars
from .vld import Func_block, Opa


class T2(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, path: str):
        raise NotImplementedError

    @property
    @abstractmethod
    def ignore(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def _get_tokens(self, block: Func_block) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def get_tokens(self) -> List[str]:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def calc_func_key(file_name: Optional[str], func_name: Optional[str],
                      class_name: Optional[str]) -> str:
        raise NotImplementedError

    @abstractmethod
    def current_key(self) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def get_func_block(self, key: str) -> Optional[Func_block]:
        raise NotImplementedError

    @abstractmethod
    def add_handlers(self,
                     extra: Dict[str, Callable[[Opa, PHP_Vars, List[Any]],
                                               Union[str, List[str]]]],
                     force=False):
        raise NotImplementedError


class OP_handlers(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, t: T2):
        raise NotImplementedError

    @property
    @abstractmethod
    def bind(self) -> T2:
        raise NotImplementedError

    @abstractmethod
    def add_handlers(self,
                     extra: Dict[str, Callable[[Opa, PHP_Vars, 'OP_handlers'],
                                               Union[str, List[str]]]],
                     force=False):
        raise NotImplementedError

    @abstractmethod
    def call(self, opa: Opa, pvars: PHP_Vars) -> Union[str, List[str]]:
        raise NotImplementedError
