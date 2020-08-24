#!/usr/bin/env python3

from php_tokenizer import Tokenizer_v2
import csv
from os import path

if __name__ == "__main__":
    ens = []
    with open(r'./entries.list') as fp:
        c = fp.read()
    ens = c.splitlines()
    token_list = []
    label_list = []
    total = len(ens)
    for i, en in enumerate(ens):
        abs_path = path.abspath(en)
        t = Tokenizer_v2(abs_path)
        print("\r{}".format(en))
        print("\r{0}/{1}".format(i + 1, total), end='')
        tks = t.get_tokens()
        token_list.append(' '.join(tks))
        if en.startswith(r'./cwe_079_samples/bad'):
            label_list.append(1)
        elif en.startswith(r'./cwe_079_samples/good'):
            label_list.append(0)
    print('')
    print('writing...')
    with open(r'datasets.csv', 'w') as csvfile:
        csv_writer = csv.writer(csvfile)
        rows = list(zip(ens, token_list, label_list))
        csv_writer.writerows(rows)
