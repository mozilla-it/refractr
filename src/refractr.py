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
from leatherman.yaml import yaml_format
from leatherman.dictionary import head, body, head_body
from leatherman.repr import __repr__
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

class LoadRefractError(Exception):
    def __init__(self, dst):
        msg = f'load refract error; dst={dst}'
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

def is_scalar(obj):
    return isinstance(obj, (str, bool, int, float))

def is_list_of_scalars(obj):
    if isinstance(obj, (list, tuple)):
        return all([is_scalar(item) for item in obj])
    return False

def is_list_of_dicts(obj):
    if isinstance(obj, (list, tuple)):
        return all([isinstance(item, dict) for item in obj])

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
        return '\n'.join([repr(stanza) for stanza in stanzas if stanza])

def startswith(s, *tests):
    result = any([s.startswith(test) for test in tests])
    return result

class Refract:
    def __init__(self, dst=None, srcs=None, nginx=None, tests=None, status=None):
        self.dst = dst
        self.srcs = srcs
        self.nginx = nginx
        self._tests = tests
        self.status = status

    @property
    def src(self):
        if self.srcs:
            return self.srcs[0]

    @property
    def server_name(self):
        return join(domains(self.srcs))

    @property
    def is_rewrite(self):
        if isinstance(self.dst, (list, tuple)):
            return any([startswith(k, '^', 'if') for d in self.dst for k,v in d.items()])
        return False

    @property
    def tests(self):
        if self._tests:
            return self._tests
        tests = {}
        if not self.is_rewrite:
            for src in self.srcs:
                given = f'http://{src}'
                if is_list_of_dicts(self.dst):
                    for item in self.dst:
                        try:
                            location, target = head_body(item)
                            tests[f'{given}{location}'] = target
                        except:
                            continue
                elif is_scalar(self.dst):
                    tests[given] = self.dst
                else:
                    raise LoadRefractError(self.dst)
        return tests

    def listen(self, port):
        return port, f'[::]:{port}'

    def __str__(self):
        json = dict(tests=self.tests)
        if self.nginx:
            json.update(dict(nginx=self.nginx))
        else:
            json = dict(srcs=self.srcs, dst=self.dst, status=self.status, tests=self.tests)
            json.update(dict(
                srcs=self.srcs,
                dst=self.dst,
                status=self.status))
        return yaml_format(json)

    def render_http_to_https(self):
        return Section(
            'server',
            kvo('server_name', self.server_name),
            dups('listen', *self.listen(HTTP_PORT)),
            kmvo('return', self.status, f'https://$host$request_uri')
        )

    def render_redirect(self):
        server_name = kvo('server_name', self.server_name)
        listen = dups('listen', *self.listen(HTTPS_PORT))
        if is_list_of_dicts(self.dst):
            locations = []
            for dst in self.dst:
                path, target = head_body(dst)
                locations += [Location(
                    path,
                    kmvo('return', self.status, target)
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

    def render_rewrite(self):
        server_name = kvo('server_name', self.server_name)
        listen = dups('listen', *self.listen(HTTPS_PORT))
        rewrites = []
        for dst in self.dst:
            if_ = dst.pop('if', None)
            return_ = kvo('return', self.status)
            match, target = head_body(dst)
            rewrite = kmvo(
                'rewrite',
                match,
                target
            )
            if if_:
                rewrite = Section(f'if ({if_})', rewrite)
            rewrites += [rewrite]
        return Section(
            'server',
            server_name,
            listen,
            *rewrites,
            return_,
        )

    def render_refract(self):
        if self.is_rewrite:
            return self.render_rewrite()
        return self.render_redirect()

    def render(self):
        return [
            self.render_http_to_https(),
            self.render_refract(),
        ]

    __repr__ = __repr__

def listify(value):
    if isinstance(value, dict):
        return value
    elif isinstance(value, (list, tuple)):
        return list(value)
    elif value != None:
        return [value]
    return value

def load_refract(spec):
    dst = spec.pop('dst', None)
    src = spec.pop('src', None)
    nginx = spec.pop('nginx', None)
    tests = spec.pop('tests', None)
    status = spec.pop('status', 301)
    if len(spec) == 1:
        dst, src = list(spec.items())[0]
    srcs = listify(src)
    return dict(dst=dst, srcs=srcs, nginx=nginx, tests=tests, status=status)

def load_refractr(config, refractr_pns=None):
    if refractr_pns == None:
        refractr_pns = ["*"]
    spec = yaml.safe_load(open(config))
    refracts = [load_refract(refract) for refract in spec['refracts']]
    spec['refracts'] = [refract for refract in refracts if fuzzy(refract['srcs']).include(*refractr_pns)]
    return RefractrConfig(spec)

def refract(config=None, output=None, refractr_pns=None, **kwargs):
    refracrt = load_refractr(config, refractr_pns)
    print(refracrt.render())
