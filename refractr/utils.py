#!/usr/bin/env python3
import sys
from collections import OrderedDict
from itertools import product
from urllib import parse

from leatherman.dbg import dbg


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def startswith(s, *tests):
    result = any([s.startswith(test) for test in tests])
    return result


def join(items, sep=" "):
    return sep.join(items)


def is_list_of_scalars(obj):
    if isinstance(obj, (list, tuple)):
        return all([is_scalar(item) for item in obj])
    return False


def is_list_of_dicts(obj):
    if isinstance(obj, (list, tuple)):
        return all([isinstance(item, dict) for item in obj])


def urlparse(url):
    if url.startswith("http"):
        return parse.urlparse(url)
    return parse.urlparse(f"http://{url}")
