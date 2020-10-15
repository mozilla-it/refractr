from leatherman.dictionary import head_body
from leatherman.repr import __repr__
from leatherman.yaml import yaml_format

from refractr.url import URL
from refractr.utils import *

WILDCARD = 'wildcard'

def tuplify(value):
    if isinstance(value, dict):
        return value
    elif isinstance(value, (list, tuple)):
        return tuple(value)
    elif value != None:
        return (value,)
    return value

def listify(obj):
    if isinstance(obj, tuple):
        return list(obj)
    return obj

class BaseRefract:
    def __init__(self, dsts=None, srcs=None, status=None, preserve_path=False, wildcard_file=None, tests=None):
        self.dsts = tuplify(dsts)
        self._srcs = tuplify(srcs)
        self.status = status
        self.preserve_path = preserve_path
        self.wildcard_file = wildcard_file
        self.tests = tuplify((tests or []) + self.generate_tests())

    def __str__(self):
        return yaml_format(self.json())

    __repr__ = __repr__

    @property
    def src(self):
        if self.srcs:
            assert isinstance(self.srcs, tuple) and len(self.srcs) > 0, type(self.srcs)
            return self.srcs[0]
        return None

    @property
    def srcs(self):
        if self.wildcard_file:
            srcs = []
            for src in self._srcs:
                if src.startswith(WILDCARD):
                    for subdomain in self.wildcard_extrapolated_subdomains:
                        src1 = subdomain + src[len(WILDCARD):]
                        srcs.append(src1)
                else:
                    srcs.append(src)
            return tuple(srcs)
        return self._srcs

    @property
    def balance(self):
        '''
        generated tests will always match location redirects
        rewrites do no generate tests; so this is to help identify that
        '''
        dst_count = len(self.dsts) if isinstance(self.dsts, list) else 1
        test_count = len(self.tests)
        return test_count - dst_count

    @property
    def wildcard_extrapolated_subdomains(self):
        return [
            line for
            line in
            open(self.wildcard_file).read().strip().split('\n')
            if not line.startswith('#')
        ]

    def json(self):
        return dict(
            dsts=listify(self.dsts),
            srcs=listify(self.srcs),
            status=self.status,
            preserve_path=self.preserve_path,
            wildcard_file=self.wildcard_file,
            tests=listify(self.tests),
        )

    @property
    def server_name(self):
        if self.wildcard_file:
            nltab = '\n' + ' '*8
            return join([nltab + URL(src).netloc for src in self.srcs])
        return join([URL(src).netloc for src in self.srcs])

    @property
    def server_name_include(self):
        return self.srcs[0] + '.include'


    def render(self):
        raise NotImplementedError
