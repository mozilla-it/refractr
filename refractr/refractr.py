import os
import tldextract

from itertools import chain

from leatherman.dictionary import head_body
from leatherman.fuzzy import fuzzy
from leatherman.repr import __repr__
from leatherman.dbg import dbg

from refractr.exceptions import *
from refractr.nginx import NginxRefract
from refractr.simple import SimpleRefract
from refractr.complex import ComplexRefract
from refractr.validate import RefractrValidator
from refractr.utils import *

DIR = os.path.dirname(__file__)

extract = tldextract.TLDExtract(
    cache_dir=f'{DIR}/.tld-cache'
)

setup_yaml()

def filter_only(refracts, only=None):
    if only:
        types = {
            'nginx': NginxRefract,
            'simple': SimpleRefract,
            'complex': ComplexRefract,
        }
        return [
            refract
            for refract
            in refracts
            if isinstance(refract, types[only])
        ]
    return refracts

def filter_sources(refracts, patterns, all_sources=False):
    src_dict = {refract.src: refract for refract in refracts}
    srcs_dict = {refract.srcs: refract for refract in refracts}
    if all_sources:
        return [
            srcs_dict[srcs]
            for srcs
            in fuzzy(list(srcs_dict.keys())).include(*patterns)
        ]
    filtered = [
        src_dict[src]
        for src
        in fuzzy(list(src_dict.keys())).include(*patterns)
    ]
    if filtered:
        return filtered
    return [
        srcs_dict[srcs]
        for srcs
        in fuzzy(list(srcs_dict.keys())).include(*patterns)
    ]

def filter_count(refracts, count=None):
    if refracts and count and abs(count) < len(refracts):
        return refracts[:count] if count > 0 else refracts[count:]
    return refracts

class Refractr:
    def __init__(self, config=None, netloc=None, early=False, verbose=None, **kwargs):
        self.validator = RefractrValidator(netloc, early, verbose)
        with open(config, 'r') as f:
            cfg = yaml.safe_load(f)
        self.default_domains = cfg.get('default-domains', [])
        self.refracts = [
            Refractr.load_refract(spec)
            for spec
            in cfg['refracts']
        ]

    __repr__ = __repr__

    @staticmethod
    def load_refract(spec):
        # this is a simple http->https redirect
        if isinstance(spec, str):
            # nginx ingress will give a 308 status code, not 301
            return SimpleRefract(f'{spec}/', spec, 308)
        tests = spec.pop('tests', None)
        nginx = spec.pop('nginx', None)
        if nginx:
            return NginxRefract(nginx, tests)
        dsts = spec.pop('dsts', None)
        srcs = spec.pop('srcs', None)
        status = spec.pop('status', 301)
        headers = spec.pop('headers', None)
        preserve_path = spec.pop('preserve-path', True)
        wildcard_file = spec.pop('wildcard-file', None)
        if len(spec) == 1:
            dsts, srcs = head_body(spec)
        if isinstance(dsts, list):
            return ComplexRefract(dsts, srcs, status, headers, preserve_path, wildcard_file, tests)
        return SimpleRefract(dsts, srcs, status, headers, preserve_path, wildcard_file)

    def _filter(self, patterns=None, only=None, count=None, all_sources=False):
        if patterns == None:
            patterns = ['*']
        # FIXME: filter on dsts targets if nothing found
        filtered = self.refracts
        filtered = filter_only(filtered, only)
        filtered = filter_sources(filtered, patterns, all_sources)
        filtered = filter_count(filtered, count)
        return filtered

    def show(self, patterns=None, only=None, count=None, all_sources=False):
        refracts = self._filter(patterns, only, count, all_sources)
        return {
            'refracts': [
                refract.json()
                for refract
                in refracts
            ],
            'refracts-count': len(refracts)
        }

    def domains(self, patterns=None, only=None, count=None, all_sources=False):
        refracts = self._filter(patterns, only, count, all_sources)
        domains = list(set(chain(*[
            refract.srcs
            for refract
            in refracts
        ]))) + self.default_domains
        def sorter(name):
            subdomain, domain, suffix = extract(name)
            sortkey = [domain, suffix]
            #this sorts by domain+suffix then subdomain in reverse order
            sortkey.append(list(reversed(subdomain.split('.'))))
            return sortkey
        return {
            'domains': sorted(domains, key=sorter),
            'domains-count': len(domains),
        }

    def render(self, patterns=None, only=None, count=None, all_sources=False):
        refracts = self._filter(patterns, only, count, all_sources)
        stanzas = list(chain(*[
            refract.render()
            for refract
            in refracts
        ]))
        return '\n'.join([
            stanza if isinstance(stanza, str) else repr(stanza)
            for stanza
            in stanzas
        ])

    def validate(self, patterns=None, only=None, count=None, all_sources=False):
        refracts = self._filter(patterns, only, count, all_sources)
        validation = self.validator.validate_refracts(refracts)
        return validation
