#!/usr/bin/env python3

from os import path
from typing import List, Union

import numpy as np
from joblib import dump
from sklearn.cluster import KMeans

from php_tokenizer import Tokenizer_v2
from php_tokenizer.common.base import OP_handlers
from php_tokenizer.common.vld import Opa
from php_tokenizer.utils.helper import PHP_Vars
from php_tokenizer.utils.sink import get_sink_features


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
    sinks = ()
    sinks_txt = __file__.replace('train_sinks.py', 'sinks.txt')
    if not path.isfile(sinks_txt):
        ens = []
        with open(r'./entries.list', encoding='utf-8') as fp:
            c = fp.read()
        ens = c.splitlines()
        total = len(ens)
        sink_list = []
        for i, en in enumerate(ens):
            abs_path = path.abspath(en)
            t = Tokenizer_v2(abs_path)
            t.add_handlers({'ECHO': raw_echo}, force=True)
            print("\r{}".format(en))
            print("\r{0}/{1}".format(i, total), end='')
            _ = t.get_tokens()
            sink_list.extend(t.sinks)
        sinks = set(sink_list)
        print('')
        print('writing...')
        with open('sinks.txt', "w", encoding='utf-8') as fp:
            for s in sinks:
                fp.write(s + '\n')
    else:
        with open('sinks.txt', 'r', encoding='utf-8') as fp:
            c = fp.read()
        sinks = c.splitlines()
    features = [get_sink_features(s) for s in sinks]
    X_std = np.array(features)
    model = KMeans(n_clusters=17, max_iter=100, tol=1e-4, verbose=2)
    model.fit(X_std)
    dump(model, 'sink_cluster_kmeans.model')
