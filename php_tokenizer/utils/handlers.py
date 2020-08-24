#!/usr/bin/env python3

from php_tokenizer.utils.sink import sink2token
import re
from typing import List, Union
from urllib.parse import unquote_plus

from ..common.base import OP_handlers
from ..common.vld import Opa
from ..utils.helper import PHP_Vars

known_filters = [
    'filter_has_var', 'filter_input', 'filter_input_array', 'filter_list',
    'filter_var_array', 'filter_var', 'addslashes', 'preg_replace',
    'htmlentities', 'htmlspecialchars', 'http_build_query',
    'mysql_real_escape_string', 'rawurlencode', 'unserialize', 'urlencode',
    'settype'
]
known_web_sources = [
    '_GET', '_POST', '_COOKIE', '_REQUEST', '_FILES', '_HTTP_RAW_POST_DATA'
]

known_ext_source = [
    'system', 'fread', 'exec', 'fgets', 'shell_exec', 'proc_open',
    'stream_get_contents'
]
known_filter_ops = ['CAST', 'CONCAT']


def _nop(opa: Opa, pvars: PHP_Vars,
         caller: OP_handlers) -> Union[str, List[str]]:
    if opa.op not in caller.bind.ignore:
        return 'NOP'
    else:
        return []


def _two_nums_calc(opa: Opa, pvars: PHP_Vars,
                   caller: OP_handlers) -> Union[str, List[str]]:
    op1 = opa.op1 if str(opa.op1_type).startswith('IS_CONST') else pvars.get(
        opa.op1, opa.op_no)
    op2 = opa.op2 if str(opa.op2_type).startswith('IS_CONST') else pvars.get(
        opa.op2, opa.op_no)
    if op1 in pvars._cvs.values() or op2 in pvars._cvs.values():
        pvars.set(opa.ret, '$_nums_{}'.format(opa.op_no), opa.op_no)
    else:
        if type(op1) is str:
            m = re.match(r'^\d+(.\d+)?', op1)
            if m:
                sub = m.span()
                op1 = op1[sub[0], sub[1]]
                op1 = float(op1) if op1.find('.') != -1 else int(op1)
            else:
                op1 = 0
        if type(op2) is str:
            m = re.match(r'^\d+(.\d+)?', op2)
            if m:
                sub = m.span()
                op2 = op2[sub[0], sub[1]]
                op2 = float(op2) if op2.find('.') != -1 else int(op2)
            else:
                op2 = 0
        if opa.op == 'ADD':
            pvars.set(opa.ret, op1 + op2, opa.op_no)
        elif opa.op == 'SUB':
            pvars.set(opa.ret, op1 - op2, opa.op_no)
        elif opa.op == 'MUL':
            pvars.set(opa.ret, op1 * op2, opa.op_no)
        elif opa.op == 'DIV':
            pvars.set(opa.ret, op1 / op2, opa.op_no)
        elif opa.op == 'MOD':
            flag = -1 if op1 < 0 else 1
            pvars.set(opa.ret, flag * (abs(op1) % abs(op2)), opa.op_no)
        elif opa.op == 'ASSIGN_ADD':
            pvars.set(opa.op1, op1 + op2, opa.op_no)
        elif opa.op == 'ASSIGN_SUB':
            pvars.set(opa.op1, op1 - op2, opa.op_no)
        elif opa.op == 'ASSIGN_MUL':
            pvars.set(opa.op1, op1 * op2, opa.op_no)
        elif opa.op == 'ASSIGN_DIV':
            pvars.set(opa.op1, op1 / op2, opa.op_no)
        elif opa.op == 'ASSIGN_MOD':
            flag = -1 if op1 < 0 else 1
            pvars.set(opa.op1, flag * (abs(op1) % abs(op2)), opa.op_no)
        else:
            raise NotImplementedError
    if opa.op not in caller.bind.ignore:
        return opa.op
    else:
        return []


def _concat(opa: Opa, pvars: PHP_Vars,
            caller: OP_handlers) -> Union[str, List[str]]:
    op1 = unquote_plus(opa.op1) if str(
        opa.op1_type).startswith('IS_CONST') else pvars.get(
            opa.op1, opa.op_no, '')
    op2 = unquote_plus(opa.op2) if str(
        opa.op2_type).startswith('IS_CONST') else pvars.get(
            opa.op2, opa.op_no, '')
    pvars.set(opa.ret, op1 + op2, opa.op_no)
    if opa.op not in caller.bind.ignore:
        return opa.op
    else:
        return []


def _rope_init(opa: Opa, pvars: PHP_Vars,
               caller: OP_handlers) -> Union[str, List[str]]:
    return _concat(opa, pvars, caller)


def _rope_add(opa: Opa, pvars: PHP_Vars,
              caller: OP_handlers) -> Union[str, List[str]]:
    return _concat(opa, pvars, caller)


def _rope_end(opa: Opa, pvars: PHP_Vars,
              caller: OP_handlers) -> Union[str, List[str]]:
    return _concat(opa, pvars, caller)


def _cast(opa: Opa, pvars: PHP_Vars,
          caller: OP_handlers) -> Union[str, List[str]]:
    op1 = pvars.get(opa.op1, opa.op_no, opa.op_no) if not str(
        opa.op1_type).startswith('IS_CONST') else unquote_plus(
            opa.op1) if type(opa.op1) is str else opa.op1
    token = None
    if opa.ext == 6:
        token = 'CAST_STR'
        if op1 not in ['<true>', '<false', '<null>']:
            op1 = str(op1)
        pvars.set(opa.ret, op1, opa.op_no)
    elif opa.ext == 4:
        token = 'CAST_INT'
        if op1 == '<false>':
            pvars.set(opa.ret, 0, opa.op_no)
        elif op1 == '<true>':
            pvars.set(opa.ret, 1, opa.op_no)
        elif type(op1) is str:
            m = re.match(r'^\d+', op1)
            if m:
                sub = m.span()
                op1 = int(op1[sub[0], sub[1]])
            else:
                op1 = 0
            pvars.set(opa.ret, op1, opa.op_no)
        elif op1 is None:
            pvars.set(opa.ret, 0, opa.op_no)
        else:
            pvars.set(opa.ret, op1, opa.op_no)
    elif opa.ext == 5:
        token = 'CAST_FLOAT'
        if op1 == '<false>':
            pvars.set(opa.ret, 0.0, opa.op_no)
        elif op1 == '<true>':
            pvars.set(opa.ret, 1.0, opa.op_no)
        elif type(op1) is str:
            m = re.match(r'^\d+(.\d)?', op1)
            if m:
                sub = m.span()
                op1 = float(op1[sub[0], sub[1]])
            else:
                op1 = 0.0
            pvars.set(opa.ret, op1, opa.op_no)
        elif op1 is None:
            pvars.set(opa.ret, 0.0, opa.op_no)
        else:
            pvars.set(opa.ret, op1, opa.op_no)
    elif opa.ext == 16:
        token = 'CAST_BOOL'
        if op1 in ['<false>', '<null>']:
            pvars.set(opa.ret, '<false>', opa.op_no)
        elif op1 == '<true>':
            pvars.set(opa.ret, '<true>', opa.op_no)
        elif op1:
            pvars.set(opa.ret, '<true>', opa.op_no)
        else:
            pvars.set(opa.ret, '<false>', opa.op_no)
    else:
        raise NotImplementedError
    if opa.op not in caller.bind.ignore:
        return token
    else:
        return []


def _new(opa: Opa, pvars: PHP_Vars,
         caller: OP_handlers) -> Union[str, List[str]]:
    c = unquote_plus(opa.op1)
    pvars.set(opa.ret, c, opa.op_no)
    pvars.append((c, '__construct'))
    pvars.new_qct()
    if opa.op not in caller.bind.ignore:
        return opa.op
    else:
        return []


def _assign(opa: Opa, pvars: PHP_Vars,
            caller: OP_handlers) -> Union[str, List[str]]:
    op2 = pvars.get(opa.op2, opa.op_no, '$__none__') if not str(
        opa.op2_type).startswith('IS_CONST') else unquote_plus(
            opa.op2) if type(opa.op2) is str else opa.op2
    pvars.set(opa.op1, op2, opa.op_no)
    if opa.op not in caller.bind.ignore:
        return opa.op
    else:
        return []


def _init_fcall(opa: Opa, pvars: PHP_Vars,
                caller: OP_handlers) -> Union[str, List[str]]:
    m = unquote_plus(
        opa.op2) if opa.op2_type.startswith('IS_CONST') else pvars.get(
            opa.op2, opa.op_no, '__UNKNOWN_METHOD')
    pvars.append((None, m))
    pvars.new_qct()
    if opa.op not in caller.bind.ignore:
        return opa.op
    else:
        return []


def _init_method_call(opa: Opa, pvars: PHP_Vars,
                      caller: OP_handlers) -> Union[str, List[str]]:
    m = unquote_plus(
        opa.op2) if opa.op2_type.startswith('IS_CONST') else pvars.get(
            opa.op2, opa.op_no, '__UNKNOWN_METHOD')
    c = pvars.get(opa.op1, opa.op_no) if opa.op1_type in [
        'IS_CV', 'IS_VAR', 'IS_TMP_VAR'
    ] else unquote_plus(opa.op1) if str(
        opa.op1).startswith('IS_CONST') else None
    pvars.append((c, m))
    pvars.new_qct()
    if opa.op not in caller.bind.ignore:
        return opa.op
    else:
        return []


def _init_fcall_by_name(opa: Opa, pvars: PHP_Vars,
                        caller: OP_handlers) -> Union[str, List[str]]:
    return _init_method_call(opa, pvars, caller)


def _do_icall(opa: Opa, pvars: PHP_Vars,
              caller: OP_handlers) -> Union[str, List[str]]:
    _, m = pvars.pop()
    pvars.set(opa.ret, '$' + m, opa.op_no)
    pvars.del_qct()
    if opa.op not in caller.bind.ignore:
        return str(m).upper()
    else:
        return []


def _do_fcall(opa: Opa, pvars: PHP_Vars,
              caller: OP_handlers) -> Union[str, List[str]]:
    c, m = pvars.pop()
    old_key = caller.bind.current_key()
    f = old_key.split(':')[0] if type(old_key) is str else None
    key = caller.bind.calc_func_key(f, m, c)
    next_block = caller.bind.get_func_block(key)
    nested = []
    if next_block:
        nested = caller.bind._get_tokens(next_block)
    else:
        pvars.del_qct()
    if opa.ret and next_block:
        tmp = pvars.pop()
        pvars.set(opa.ret, tmp, opa.op_no)
    elif opa.ret:
        pvars.set(opa.ret, '$' + m, opa.op_no)
    if opa.op not in caller.bind.ignore:
        nested.insert(0, str(m).upper())
    return nested


def _send_val(opa: Opa, pvars: PHP_Vars,
              caller: OP_handlers) -> Union[str, List[str]]:
    op1 = unquote_plus(opa.op1) if type(opa.op1) is str else opa.op1
    pvars.send(op1)
    if opa.op not in caller.bind.ignore:
        return opa.op
    else:
        return []


def _send_var(opa: Opa, pvars: PHP_Vars,
              caller: OP_handlers) -> Union[str, List[str]]:
    op1 = pvars.get(opa.op1, opa.op_no, '$__none__')
    pvars.send(op1)
    if opa.op not in caller.bind.ignore:
        return opa.op
    else:
        return []


def _send_ref(opa: Opa, pvars: PHP_Vars,
              caller: OP_handlers) -> Union[str, List[str]]:
    return _send_var(opa, pvars, caller)


def _recv(opa: Opa, pvars: PHP_Vars,
          caller: OP_handlers) -> Union[str, List[str]]:
    pvars.set(opa.ret, pvars.recv(), opa.op_no)
    if opa.op not in caller.bind.ignore:
        return opa.op
    else:
        return []


def _recv_init(opa: Opa, pvars: PHP_Vars,
               caller: OP_handlers) -> Union[str, List[str]]:
    op2 = unquote_plus(opa.op2) if type(opa.op2) is str else opa.op2
    pvars.set(opa.ret, pvars.recv(op2), opa.op_no)
    if opa.op not in caller.bind.ignore:
        return opa.op
    else:
        return []


def _return(opa: Opa, pvars: PHP_Vars,
            caller: OP_handlers) -> Union[str, List[str]]:
    pvars.del_qct()
    if opa.ret:
        res = opa.ret if type(opa.ret) is not str else unquote_plus(
            opa.ret) if opa.ret.startswith('IS_CONST') else pvars.get(
                opa.ret, opa.op_no)
        pvars.append(res)
    if opa.op not in caller.bind.ignore:
        return opa.op
    else:
        return []


def _fetch_const(opa: Opa, pvars: PHP_Vars,
                 caller: OP_handlers) -> Union[str, List[str]]:
    op2 = unquote_plus(opa.op2) if type(opa.op2) is str else opa.op2
    pvars.set(opa.ret, op2, opa.op_no)
    if opa.op not in caller.bind.ignore:
        return opa.op
    else:
        return []


def _fetch_(opa: Opa, pvars: PHP_Vars,
            caller: OP_handlers) -> Union[str, List[str]]:
    token = opa.op1[
        1:] if opa.fetch == 'global' and opa.op1 in known_web_sources else opa.op
    op1 = opa.op1 if type(opa.op1) is not str else unquote_plus(
        opa.op1) if opa.op1_type.startswith('IS_CONST') else pvars.get(
            opa.op1, opa.op_no, '$__none__')
    pvars.set(opa.ret, op1, opa.op_no)
    if opa.op not in caller.bind.ignore:
        return token
    else:
        return []


def _fetch_r(opa: Opa, pvars: PHP_Vars,
             caller: OP_handlers) -> Union[str, List[str]]:
    return _fetch_(opa, pvars, caller)


def _fetch_w(opa: Opa, pvars: PHP_Vars,
             caller: OP_handlers) -> Union[str, List[str]]:
    return _fetch_(opa, pvars, caller)


def _fetch_wr(opa: Opa, pvars: PHP_Vars,
              caller: OP_handlers) -> Union[str, List[str]]:
    return _fetch_(opa, pvars, caller)


def _echo(opa: Opa, pvars: PHP_Vars,
          caller: OP_handlers) -> Union[str, List[str]]:
    token = 'ECHO_CONST' if opa.op1_type.startswith('IS_CONST') else pvars.get(
        opa.op1, opa.op_no, '$__none__')
    if token != 'ECHO_CONST':
        token = sink2token(token)
    if opa.op not in caller.bind.ignore:
        return token
    else:
        return []


builtin_handlers = {
    'NOP': _nop,
    'ADD': _two_nums_calc,
    'SUB': _two_nums_calc,
    'MUL': _two_nums_calc,
    'DIV': _two_nums_calc,
    'MOD': _two_nums_calc,
    'ASSIGN_ADD': _two_nums_calc,
    'ASSIGN_SUB': _two_nums_calc,
    'ASSIGN_MUL': _two_nums_calc,
    'ASSIGN_DIV': _two_nums_calc,
    'ASSIGN_MOD': _two_nums_calc,
    'CONCAT': _concat,
    'ROPE_INIT': _rope_init,
    'ROPE_ADD': _rope_add,
    'ROPE_END': _rope_end,
    'CAST': _cast,
    'NEW': _new,
    'ASSIGN': _assign,
    'INIT_FCALL': _init_fcall,
    'INIT_METHOD_CALL': _init_method_call,
    'INIT_FCALL_BY_NAME': _init_fcall_by_name,
    'DO_ICALL': _do_icall,
    'DO_FCALL': _do_fcall,
    'SEND_VAL': _send_val,
    'SEND_VAR': _send_var,
    'SEND_VAR_EX': _send_var,
    'SEND_REF': _send_ref,
    'RECV': _recv,
    'RECV_INIT': _recv_init,
    'RETURN': _return,
    'FETCH_CONSTANT': _fetch_const,
    'FETCH_R': _fetch_r,
    'FETCH_W': _fetch_w,
    'FETCH_WR': _fetch_wr,
    'ECHO': _echo
}
