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


setup_yaml()

class Refractr:
    def __init__(self, config=None, netloc=None, early=False, verbose=None, **kwargs):
        self.validator = RefractrValidator(netloc, early, verbose)
        with open(config, 'r') as f:
            cfg = yaml.safe_load(f)
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
            return SimpleRefract(spec, [spec], 301)
        tests = spec.pop('tests', None)
        nginx = spec.pop('nginx', None)
        if nginx:
            return NginxRefract(nginx, tests)
        dst = spec.pop('dst', None)
        srcs = spec.pop('srcs', None)
        status = spec.pop('status', 301)
        if len(spec) == 1:
            dst, srcs = head_body(spec)
        srcs = listify(srcs)
        if isinstance(dst, list):
            return ComplexRefract(dst, srcs, status, tests)
        return SimpleRefract(dst, srcs, status)

    def _filter(self, patterns=None, only=None, count=None):
        if patterns == None:
            patterns = ['*']
        if only:
            # FIXME: filter on dst targets if nothing found
            types = {
                'nginx': NginxRefract,
                'simple': SimpleRefract,
                'complex': ComplexRefract,
            }
            filtered = [
                refract
                for refract
                in self.refracts
                if isinstance(refract, types[only])
            ]
        else:
            filtered = self.refracts
        filtered = [
            refract
            for refract
            in filtered
            if fuzzy(refract.srcs).include(*patterns)
        ]
        if filtered and count and abs(count) < len(filtered):
            filtered = filtered[:count] if count > 0 else filtered[count:]
        return filtered

    def show(self, patterns=None, only=None, count=False):
        refracts = self._filter(patterns, only, count)
        return {
            'refracts': [
                refract.json()
                for refract
                in refracts
            ],
            'refracts-count': len(refracts)
        }

    def domains(self, patterns=None, only=None, count=False):
        refracts = self._filter(patterns, only, count)
        domains = sorted(list(set(chain(*[
            refract.srcs
            for refract
            in refracts
        ]))))
        return {
            'domains': domains,
            'domains-count': len(domains),
        }

    def render(self, patterns=None, only=None, count=False):
        refracts = self._filter(patterns, only, count)
        stanzas = list(chain(*[
            refract.render()
            for refract
            in refracts
        ]))
        [type(stanza) for stanza in stanzas]
        return '\n'.join([
            stanza if isinstance(stanza, str) else repr(stanza)
            for stanza
            in stanzas
        ])

    def validate(self, patterns=None, only=None, count=None):
        refracts = self._filter(patterns, only, count)
        validation = self.validator.validate_refracts(refracts)
        return validation
