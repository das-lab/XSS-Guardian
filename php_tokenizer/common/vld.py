#!/usr/bin/env python3

from functools import reduce
from typing import Any, Iterable, List, Optional, Union
import json
import os
import subprocess
import sys

vld_detect_command = [r'php', r'-ini']
opa_keys = [
    'line', '#', '*', 'E', 'I', 'O', 'op_code', 'op', 'fetch', 'ext',
    'return_type', 'return', 'op1_type', 'op1', 'op2_type', 'op2',
    'ext_op_type', 'ext_op'
]
br_keys = ['sline', 'eline', 'sop', 'eop', 'outs']


def check_vld() -> bool:
    '''
    Check the existence of json patched vld.
    '''
    vld_found = False
    php = 'php.exe' if sys.platform == 'win32' else 'php'
    path = os.getenv('PATH')
    if not path:
        return False
    search_path = path.split(os.pathsep)
    for d in search_path:
        target = os.path.join(d, php)
        if os.path.isfile(target):
            vld_found = True
            break
    if not vld_found:
        return False
    p = subprocess.Popen(vld_detect_command, stdout=subprocess.PIPE)
    outs, _ = p.communicate()
    if outs and outs.find('vld.dump_json'.encode('ascii')) != -1:
        return True
    return False


class Opa(object):
    '''
    Opa means 'PHP OP Array', picked from json-patched vld output.
    '''
    def __init__(self, op_array: Iterable[Union[int, str, None]]):
        '''
        Convert the op array from python iterable to object.
        The order correctness of cols in op_array is guarateed by the caller.
        '''
        assert (18 == len(op_array))
        self.line_no: Optional[int] = op_array[0]
        self.op_no: int = op_array[1]
        self.is_dead: bool = True if op_array[2] else False
        self.E: bool = True if op_array[3] else False
        self.I: bool = True if op_array[4] else False
        self.O: bool = True if op_array[5] else False
        self.op_code: int = op_array[6]
        self.op: str = op_array[7]
        self.fetch: Optional[str] = op_array[8]
        self.ext: Union[str, int, None] = op_array[9]
        self.ret_type: Optional[str] = op_array[10]
        self.ret: Union[str, int, None] = op_array[11]
        self.op1_type: Optional[str] = op_array[12]
        self.op1: Union[str, int, None] = op_array[13]
        self.op2_type: Optional[str] = op_array[14]
        self.op2: Union[str, int, None] = op_array[15]
        self.ext_op_type: Optional[str] = op_array[16]
        self.ext_op: Union[str, int, None] = op_array[17]


class Branch(object):
    '''
    PHP branch info.
    '''
    def __init__(self, br_array: Iterable[Union[int, List[int]]]):
        '''
        Convert the branch info from python iterable to object.
        The order correctness of cols in br_array is guarateed by the caller.
        '''
        assert (5 == len(br_array))
        self.start_line_no: int = br_array[0]
        self.end_line_no: int = br_array[1]
        self.start_op_no: int = br_array[2]
        self.end_op_no: int = br_array[3]
        self.outs: List[int] = [out for out in br_array[4] if out != -2]


class Func_block(object):
    '''
    A Func_block instance representes a vld fucntion.
    '''
    def __init__(self, vld_json):
        '''
        Convert the vld output from json to python object.
        Type hint correctness of attributes is guarateed by vld implement.
        '''
        self.class_name: Optional[str] = vld_json['class']
        self.file_name: Optional[str] = vld_json['filename']
        self.function_name: Optional[str] = vld_json['function name']
        self.num_of_ops: int = vld_json['number of ops']
        self.compiled_vars: List[str] = vld_json['compiled vars']
        ops = vld_json['ops']
        self.op_arrays = [
            Opa(opa) for opa in zip(*[ops[key] for key in opa_keys])
        ]
        assert (self.num_of_ops == len(self.op_arrays))
        self.paths: List[List[int]] = vld_json['path']
        brs = vld_json['branch']
        self.branches = [
            Branch(br) for br in zip(*[brs[key] for key in br_keys])
        ]
        self.vtags = self._calc_vtags()

    def _is_in_path(self, op_no: int, path: Iterable[int]) -> bool:
        last_outs = []
        for sop in path:
            sops = [b.start_op_no for b in self.branches]
            if sop not in sops:
                return False
            sub = sops.index(sop)
            if last_outs and sop not in last_outs:
                return False
            last_outs = self.branches[sub].outs
            if sop <= op_no <= self.branches[sub].end_op_no:
                return True
        return False

    def _calc_vtag(self, op_no: int) -> int:
        paths_bits_map = [
            self._is_in_path(op_no, path).bit_length() for path in self.paths
        ]
        tag = reduce(lambda x, y: (x << 1) + y, paths_bits_map, 0)
        return tag

    def _calc_vtags(self) -> List[int]:
        tags = [self._calc_vtag(opa.op_no) for opa in self.op_arrays]
        return tags


class VLD(object):
    def __init__(self, src_path: str):
        self._src: str = src_path
        self._raw: bytes = b''
        self._run()
        self._json_blocks = json.loads(self._raw)
        self._blocks = [Func_block(b) for b in self._json_blocks]
        self.vld = None

    def _run(self):
        if self._raw:
            return  # Only run once.
        out_size = os.path.getsize(self._src)
        vld_command = [
            r'php', '-dvld.active=1', r'-dvld.execute=0', r'-dvld.verbosity=3',
            r'-dvld.dump_json=1', self._src
        ]
        p = subprocess.Popen(vld_command,
                             bufsize=out_size * 12,
                             stdout=subprocess.PIPE)
        outs, _ = p.communicate()
        if outs:
            self._raw = outs

    @property
    def func_blocks_json(self) -> Any:
        return self._json_blocks

    @property
    def func_blocks(self):
        return self._blocks

    def __iter__(self):
        return iter(self._blocks)
