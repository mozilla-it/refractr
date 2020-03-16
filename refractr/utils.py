#!/usr/bin/env python3

import os
import re
import sys
import requests

from ruamel import yaml
from itertools import product
from urllib import parse
from urllib.parse import ParseResult
from collections import OrderedDict
from nginx.config.helpers import duplicate_options
from nginx.config.api import KeyOption as ko
from nginx.config.api import KeyValueOption as kvo
from nginx.config.api import Config, Section, Location, KeyMultiValueOption

from leatherman.dbg import dbg

def setup_yaml():
    """ https://stackoverflow.com/a/8661021 """
    represent_dict_order = lambda self, data: self.represent_mapping(
        "tag:yaml.org,2002:map", data.items()
    )
    yaml.add_representer(OrderedDict, represent_dict_order)

def startswith(s, *tests):
    result = any([s.startswith(test) for test in tests])
    return result

def listify(value):
    if isinstance(value, dict):
        return value
    elif isinstance(value, (list, tuple)):
        return list(value)
    elif value != None:
        return [value]
    return value

def join(items, sep=' '):
    return sep.join(items)

def dups(*args):
    arg, *args = args
    return duplicate_options(arg, args)

def kmvo(*args):
    arg, *args = args
    return KeyMultiValueOption(arg, args)

def replace(pr, **kwargs):
    return ParseResult(
        scheme=kwargs.get('scheme', pr.scheme),
        netloc=kwargs.get('netloc', pr.netloc),
        path=kwargs.get('path', pr.path),
        params=kwargs.get('params', pr.params),
        query=kwargs.get('query', pr.query),
        fragment=kwargs.get('fragment', pr.fragment))

def status_to_word(status):
    return {
        301: 'permanent',
        302: 'temporary',
    }[status]

def is_scalar(obj):
    return isinstance(obj, (str, bool, int, float))

def is_list_of_scalars(obj):
    if isinstance(obj, (list, tuple)):
        return all([is_scalar(item) for item in obj])
    return False

def is_list_of_dicts(obj):
    if isinstance(obj, (list, tuple)):
        return all([isinstance(item, dict) for item in obj])

def urlparse(url):
    if url.startswith('http'):
        return parse.urlparse(url)
    return parse.urlparse(f'http://{url}')

def domains(urls):
    return [urlparse(url)[1] for url in urls]

def domains_paths(urls):
    pairs = [urlparse(url)[1:3] for url in urls]
    domains, paths = zip(*pairs)
    domains = tuple(set(domains))
    paths = tuple(set(paths))
    if sorted(pairs) == sorted(product(domains, paths)):
        return domains, paths
    raise DomainPathMismatchError(domains, paths)

def execute_hop(given, headers=None):
    response = requests.get(given.geturl(), headers=headers, allow_redirects=False)
    location = response.headers.get('Location', None)
    if location:
        location = urlparse(location)
        if location.netloc == '':
            location = replace(location, netloc=given.netloc)
        return location, response.status_code
    return None, None

def follow_hops(given, expect, headers=None):
    matched = False
    results= []
    url1 = given
    while url1:
        url2, status = execute_hop(url1, headers)
        if url2:
            result = f'{status} {url1.geturl()} -> {url2.geturl()}'
            if url2 == expect:
                result += ' MATCH'
                matched = True
            results +=[result]
            url1 = url2
            continue
        break
    if not matched:
        results[-1] += ' MISMATCH'
    return results

def validate_hop(given, expect, status, headers=None):
    location, status_code = execute_hop(given, headers)
    assert status_code == status
    assert location == expect
    return location
