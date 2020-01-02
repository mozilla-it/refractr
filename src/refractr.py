#!/usr/bin/env python3

import os
import sys
import toml

from ruamel import yaml
from addict import Dict
from urllib import parse
from tldextract import extract
from itertools import chain, product
from collections import OrderedDict
from nginx.config.helpers import duplicate_options
from nginx.config.api import KeyOption as ko
from nginx.config.api import KeyValueOption as kvo
from nginx.config.api import KeyMultiValueOption
from nginx.config.api import Config, Section, Location

from leatherman.fuzzy import fuzzy
from leatherman.dictionary import head, body, head_body
from leatherman.dbg import dbg

HTTP_PORT = 8080
HTTPS_PORT = 8443

class DomainPathMismatchError(Exception):
    def __init__(self, domains, paths):
        msg = f'domains|paths mismatch error; the product must match; domains={domains} paths={paths}'
        super().__init__(msg)

def dups(*args):
    arg, *args = args
    return duplicate_options(arg, args)

def kmvo(*args):
    arg, *args = args
    return KeyMultiValueOption(arg, args)

def tuplify(value):
    if isinstance(value, dict):
        return value
    elif isinstance(value, (list, tuple)):
        return tuple(value)
    elif value != None:
        return (value,)
    return value

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

def join(items, sep=' '):
    return sep.join(items)

def setup_yaml():
    """ https://stackoverflow.com/a/8661021 """
    represent_dict_order = lambda self, data: self.represent_mapping(
        "tag:yaml.org,2002:map", data.items()
    )
    yaml.add_representer(OrderedDict, represent_dict_order)

setup_yaml()


class RefractSpecError(Exception):
    def __init__(self, spec):
        msg = f'refract spec error; spec={spec}'
        super().__init__(msg)


class RefractrConfig:
    def __init__(self, spec):
        self.refracts = [Refract(spec) for spec in spec.refracts]

    def render(self):
        stanzas = list(chain(*[refract.render() for refract in self.refracts]))
        return '\n'.join([repr(stanza) for stanza in stanzas])

class Refract:
    def __init__(self, spec):
        assert spec and isinstance(spec, dict), 'error: non-dict or empty passed as spec'
        nginx = spec.pop('nginx', None)
        src = spec.get('src', None)
        dst = spec.get('dst', None)
        status = spec.get('status', 301)
        if len(spec) == 1:
            dst, src = list(spec.items())[0]
        srcs = tuplify(src)
        dsts = tuplify(dst)
        domains, paths = domains_paths(srcs)
        if paths != ('',):
            dsts = dict(zip(paths, dsts))
        self.nginx = nginx
        self.srcs = domains
        self.dsts = dsts
        self.status = status

    @property
    def src(self):
        if self.srcs:
            return self.srcs[0]

    @property
    def dst(self):
        if self.dsts:
            return self.dsts[0]

    @property
    def server_name(self):
        return join(domains(self.srcs))

    def listen(self, port):
        return port, f'[::]:{port}'

    def __repr__(self):
        fields = ', '.join([
            f'nginx={self.nginx}',
            f'srcs={self.srcs}',
            f'dsts={self.dsts}',
            f'status={self.status}',
        ])
        return f'{self.__class__.__name__}({fields})'

    def render_http_to_https(self):
        return Section(
            'server',
            kvo('server_name', self.server_name),
            dups('listen', *self.listen(HTTP_PORT)),
            kmvo('return', self.status, f'https://$server_name$request_uri')
        )

    def render_refract(self):
        server_name = kvo('server_name', self.server_name)
        listen = dups('listen', *self.listen(HTTPS_PORT))
        if isinstance(self.dsts, dict):
            locations = []
            for path, dst in self.dsts.items():
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


def load_yaml(config):
    spec = yaml.safe_load(open(config))
    return Dict(spec)


def refract(config=None, output=None, redirect_pns=None, **kwargs):
    spec = load_yaml(config)
    config = RefractrConfig(spec)
    print(config.render())
