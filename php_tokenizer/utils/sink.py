#!/usr/bin/env python3
from typing import Union
from . import SINK_TYPE_DICT
from ..model import sink_cluster_model
import re
import numpy as np


def dollar_index(sink: str) -> int:
    return sink.find('$')


def length_of_sink(sink: str) -> int:
    return len(sink)


def count_angle(sink: str) -> int:
    return sink.count('<')


def count_brace(sink: str) -> int:
    return sink.count('{')


def count_double_quotes(sink: str) -> int:
    return sink.count('"')


def count_single_quotes(sink: str) -> int:
    return sink.count("'")


def count_slash(sink: str) -> int:
    return sink.count('/')


def count_anti_slash(sink: str) -> int:
    return sink.count("\\")


def count_parenthesis(sink: str) -> int:
    return sink.count('(')


def count_colon(sink: str) -> int:
    return sink.count(':')


def dollar_inside_angle(sink: str) -> int:
    if re.match(r".*?<.*?\$\w.*?>.*?", sink):
        return 1
    else:
        return 0


def dollar_inside_paren(sink: str) -> int:
    if re.match(r".*?\(.*?\$\w.*?\).*?", sink):
        return 1
    else:
        return 0


def dollar_inside_brace(sink: str) -> int:
    if re.match(r".*?\{.*?\$\w.*?\}.*?", sink):
        return 1
    else:
        return 0


def dollar_behind_colon(sink: str) -> int:
    if re.match(r".*?:.*?\$\w.*?", sink):
        return 1
    else:
        return 0


feature_func_list = [
    dollar_index, count_angle, count_brace, count_double_quotes,
    count_single_quotes, count_slash, count_anti_slash, count_parenthesis,
    dollar_inside_angle, dollar_inside_brace, dollar_inside_paren, count_colon,
    dollar_behind_colon
]


def get_sink_features(sink: str) -> list:
    feature_list = []
    for func in feature_func_list:
        feature_list.append(func(sink))
    return feature_list


def sink2token(sink: str) -> str:
    features = np.array(get_sink_features(sink))
    c = sink_cluster_model.predict(features.reshape(1, -1))
    return SINK_TYPE_DICT[c[0]]


def get_sink(path: str, lineno: int) -> Union[None, str]:
    pat = r'\s*echo\s*(.*?)\s*;'
    sl = None
    with open(path, encoding='utf-8') as fp:
        cl = 0
        for line in fp:
            cl += 1
            if cl == lineno:
                sl = re.findall(pat, line)
    if sl:
        return sl[0]
    else:
        return None


__all__ = ['sink2token', 'get_sink']
