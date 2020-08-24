#!/usr/bin/env python3

from typing import List, Union
from php_tokenizer.common.base import OP_handlers
from php_tokenizer.utils.helper import PHP_Vars
from php_tokenizer.common.vld import Opa
from php_tokenizer import Tokenizer_v2
from os import path


def raw_echo(opa: Opa, pvars: PHP_Vars,
             caller: OP_handlers) -> Union[str, List[str]]:
    token = 'ECHO_CONST' if opa.op1_type.startswith('IS_CONST') else pvars.get(
        opa.op1, opa.op_no, '$__none__')
    if opa.op not in caller.bind.ignore:
        caller.bind.sinks.append(token)
        return token
    else:
        return []


if __name__ == "__main__":
    ens = []
    with open(r'./entries.list') as fp:
        c = fp.read()
    ens = c.splitlines()
    token_list = []
    label_list = []
    sinks = []
    total = len(ens)
    for i, en in enumerate(ens):
        abs_path = path.abspath(en)
        t = Tokenizer_v2(abs_path)
        t.add_handlers({'ECHO': raw_echo}, force=True)
        print("\r{}".format(en))
        print("\r{0}/{1}".format(i, total), end='')
        tks = t.get_tokens()
        token_list.append(' '.join(tks))
        if en.startswith(r'./cwe_079_samples/bad'):
            label_list.append(1)
        elif en.startswith(r'./cwe_079_samples/good'):
            label_list.append(0)
        sinks.extend(t.sinks)
    print('')
    print('writing...')
    with open('sinks.txt', "w", encoding='utf-8') as fp:
        ss = set(sinks)
        for s in ss:
            fp.write(s + '\n')
