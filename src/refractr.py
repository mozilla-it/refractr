#!/usr/bin/env python3

import os
import sys
import toml

from urllib import parse
from itertools import chain, product
from ruamel import yaml
from collections import OrderedDict
from nginx.config.helpers import duplicate_options
from nginx.config.api import KeyOption as ko
from nginx.config.api import KeyValueOption as kvo
from nginx.config.api import Config, Section, Location, KeyMultiValueOption

from leatherman.fuzzy import fuzzy
from leatherman.dictionary import head, body, head_body
from leatherman.dbg import dbg

def setup_yaml():
    """ https://stackoverflow.com/a/8661021 """
    represent_dict_order = lambda self, data: self.represent_mapping(
        "tag:yaml.org,2002:map", data.items()
    )
    yaml.add_representer(OrderedDict, represent_dict_order)

setup_yaml()

HTTP_PORT = 80
HTTPS_PORT = 443

class DomainPathMismatchError(Exception):
    def __init__(self, domains, paths):
        msg = f'domains|paths mismatch error; the product must match; domains={domains} paths={paths}'
        super().__init__(msg)

class RefractSpecError(Exception):
    def __init__(self, spec):
        msg = f'refract spec error; spec={spec}'
        super().__init__(msg)

def join(items, sep=' '):
    return sep.join(items)

def dups(*args):
    arg, *args = args
    return duplicate_options(arg, args)

def kmvo(*args):
    arg, *args = args
    return KeyMultiValueOption(arg, args)

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

class RefractrConfig:
    def __init__(self, spec):
        self.refracts = [Refract(**spec) for spec in spec['refracts']]

    def render(self):
        stanzas = list(chain(*[refract.render() for refract in self.refracts]))
        return '\n'.join([repr(stanza) for stanza in stanzas])

class Refract:
    def __init__(self, dst=None, srcs=None, nginx=None, tests=None, status=None):
        self.dst = dst
        self.srcs = srcs
        self.nginx = nginx
        self.tests = tests
        self.status = status

    @property
    def src(self):
        if self.srcs:
            return self.srcs[0]

    @property
    def server_name(self):
        return join(domains(self.srcs))

    def listen(self, port):
        return port, f'[::]:{port}'

    def __repr__(self):
        fields = ', '.join([
            f'dst={self.dst}',
            f'srcs={self.srcs}',
            f'nginx={self.nginx}',
            f'tests={self.tests}',
            f'status={self.status}',
        ])
        return f'{self.__class__.__name__}({fields})'

    def render_http_to_https(self):
        return Section(
            'server',
            kvo('server_name', self.server_name),
            dups('listen', *self.listen(HTTP_PORT)),
            kmvo('return', self.status, f'https://$host$request_uri')
        )

    def render_refract(self):
        server_name = kvo('server_name', self.server_name)
        listen = dups('listen', *self.listen(HTTPS_PORT))
        if isinstance(self.dst, dict):
            locations = []
            for path, dst in self.dst.items():
                locations += [Location(
                    path,
                    kmvo('return', self.status, dst)
                )]
            return Section(
                'server',
                server_name,
                listen,
                *locations,
            )

        return Section(
            'server',
            server_name,
            listen,
            kmvo('return', self.status, self.dst),
        )

    def render(self):
        return [
            self.render_http_to_https(),
            self.render_refract(),
        ]

def tuplify(value):
    if isinstance(value, dict):
        return value
    elif isinstance(value, (list, tuple)):
        return tuple(value)
    elif value != None:
        return (value,)
    return value

def load_refract(spec):
    dst = spec.pop('dst', None)
    src = spec.pop('src', None)
    nginx = spec.pop('nginx', None)
    tests = spec.pop('tests', {})
    status = spec.pop('status', 301)
    if len(spec) == 1:
        dst, src = list(spec.items())[0]
    srcs = tuplify(src)
    for src in srcs:
        given = f'http://{src}'
        try:
            for loc, dst_ in dst.items():
                tests[f'{given}{loc}'] = dst_
        except AttributeError:
            tests[given] = dst
    return dict(dst=dst, srcs=srcs, nginx=nginx, tests=tests, status=status)

def load_refractr(config):
    spec = yaml.safe_load(open(config))
    spec['refracts'] = [load_refract(refract) for refract in spec['refracts']]
    return RefractrConfig(spec)

def refract(config=None, output=None, redirect_pns=None, **kwargs):
    refracrt = load_refractr(config)
    print(refracrt.render())
