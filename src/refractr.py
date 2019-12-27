#!/usr/bin/env python3

import os
import sys
import toml

from ruamel import yaml
from addict import Dict
from urllib import parse
from tldextract import extract
from itertools import chain
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

def dups(*args):
    arg, *args = args
    return duplicate_options(arg, args)

def kmvo(*args):
    arg, *args = args
    return KeyMultiValueOption(arg, args)

def tuplify(value):
    if isinstance(value, (list, tuple)):
        return tuple(value)
    elif value != None:
        return (value,)
    return value

def urlparse(url):
    if url.startswith('http'):
        return parse.urlparse(url)
    return parse.urlparse(f'scheme://{url}')

def domains(urls):
    return [urlparse(url)[1] for url in urls]

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
        self.refracts = list(chain(*[Refract.create(spec).render() for spec in spec.refracts]))

    def render(self):
        return '\n'.join([repr(refract) for refract in self.refracts])

class Refract:
    @staticmethod
    def create(spec):
        assert isinstance(spec, dict), 'error: non-dict passed as spec to Refract.create'
        raw = spec.pop('raw', None)
        src = spec.pop('src', None)
        rewrite = spec.pop('rewrite', None)
        redirect = spec.pop('redirect', None)
        status = spec.pop('status', 301)
        if raw:
            return RawNginx(raw)
        if src:
            if rewrite:
                return Rewrite(rewrite, src, status)
            elif redirect:
                return Redirect(redirect, src, status)
            raise RefractSpecError(spec)
        elif len(spec) == 1:
            dst, src = list(spec.items())[0]
            return Redirect(dst, src, status)
        raise RefractSpecError(spec)

    def __init__(self, dst=None, src=None, status=None):
        self.dsts = tuplify(dst) or ()
        self.srcs = tuplify(src) or ()
        self.status = status

    def __repr__(self):
        fields = ', '.join([
            f'dsts={self.dsts}',
            f'srcs={self.srcs}',
            f'satus={self.status}',
        ])
        return f'{self.__class__.__name__}({fields})'

    @property
    def src(self):
        if self.srcs:
            return self.srcs[0]

    @property
    def dst(self):
        if self.dsts:
            return self.dsts[0]

class RawNginx(Refract):
    def __init__(self, raw):
        self.raw = raw

    def render(self):
        class RawNginxObject:
            def __repr__(self_):
                return self.raw
        return [RawNginxObject()]

    def __repr__(self):
        fields = ', '.join([
            f'raw={"yes" if self.raw else "no"}',
        ])
        return f'{self.__class__.__name__}({fields})'


class Redirect(Refract):
    def __init__(self, dst, src, status):
        super().__init__(dst, src, status)

    def render_ssl_redirect(self):
        return Section(
            'server',
            dups('listen', HTTP_PORT, f'[::]:{HTTP_PORT}'),
            kvo('server_name', join(domains(self.srcs))),
            kmvo('return', self.status, f'https://$server_name$request_uri'))

    def render_redirect(self):
        scheme, netloc, path, params, query, fragment = urlparse(self.src)
        listen = dups('listen', HTTPS_PORT, f'[::]:{HTTPS_PORT}')
        server_name = kvo('server_name', join(domains(self.srcs)))
        return_ = kmvo('return', self.status, self.dst)
        if path:
            return Section(
                'server',
                listen,
                server_name,
                Location(
                    path,
                    return_)
            )

        return Section(
            'server',
            listen,
            server_name,
            return_)

    def render(self):
        return [
            self.render_ssl_redirect(),
            self.render_redirect(),
        ]


class Rewrite(Refract):
    def __init__(self, dst, src, status):
        super().__init__(dst, src, status)

    def render(self):
        pass


def load_yaml(config):
    spec = yaml.safe_load(open(config))
    return Dict(spec)


def refract(config=None, output=None, redirect_pns=None, **kwargs):
    spec = load_yaml(config)
    config = RefractrConfig(spec)
    print(config.render())

