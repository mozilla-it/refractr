from itertools import chain

from leatherman.dictionary import head_body
from leatherman.fuzzy import fuzzy
from leatherman.repr import __repr__
from leatherman.dbg import dbg

from refractr.exceptions import *
from refractr.nginx import NginxRefract
from refractr.simple import SimpleRefract
from refractr.redirect import RedirectRefract
from refractr.rewrite import RewriteRefract
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
        if is_scalar(spec):
            return SimpleRefract(spec, listify(spec), 301)
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
            if any([startswith(k, '^', 'if') for item in dst for k, v in item.items()]):
                return RewriteRefract(dst, srcs, status, tests)
            return RedirectRefract(dst, srcs, status, tests)
        return SimpleRefract(dst, srcs, status)

    def _filter(self, refractr_pns=None, only=None, one=None):
        if refractr_pns == None:
            refractr_pns = ['*']
        if only:
            # FIXME: filter on dst targets if nothing found
            types = dict(
                nginx=NginxRefract,
                simple=SimpleRefract,
                redirect=RedirectRefract,
                rewrite=RewriteRefract,
            )
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
            if fuzzy(refract.srcs).include(*refractr_pns)
        ]
        if filtered and one:
            if one == 'first':
                return [filtered[0]]
            elif one == 'last':
                return [filtered[-1]]
        return filtered

    def show(self, refractr_pns=None, only=None, one=False):
        refracts = self._filter(refractr_pns, only, one)
        return {
            'refracts': [
                refract.json()
                for refract
                in refracts
            ],
            'refracts-count': len(refracts)
        }

    def domains(self, refractr_pns=None, only=None, one=False):
        refracts = self._filter(refractr_pns, only, one)
        domains = sorted(list(set(chain(*[
            refract.srcs
            for refract
            in refracts
        ]))))
        return {
            'domains': domains,
            'domains-count': len(domains),
        }

    def render(self, refractr_pns=None, only=None, one=False):
        refracts = self._filter(refractr_pns, only, one)
        stanzas = list(chain(*[
            refract.render()
            for refract
            in refracts
        ]))
        return '\n'.join([
            repr(stanza)
            for stanza
            in stanzas
        ])

    def validate(self, refractr_pns=None, only=None, one=None):
        refracts = self._filter(refractr_pns, only, one)
        validation = self.validator.validate_refracts(refracts)
        return validation
