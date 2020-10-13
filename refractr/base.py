from leatherman.dictionary import head_body
from leatherman.repr import __repr__
from leatherman.yaml import yaml_format

from refractr.url import URL
from refractr.utils import *

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
    def __init__(self, dsts=None, srcs=None, status=None, preserve_path=False, tests=None):
        self.dsts = tuplify(dsts)
        self.srcs = tuplify(srcs)
        self.status = status
        self.preserve_path = preserve_path
        self.tests = tuplify((tests or []) + self.generate_tests())

    def __str__(self):
        return yaml_format(self.json())

    __repr__ = __repr__

    @property
    def src(self):
        if self.srcs:
            assert isinstance(self.srcs, tuple) and len(self.srcs) > 0
            return self.srcs[0]
        return None

    @property
    def balance(self):
        '''
        generated tests will always match location redirects
        rewrites do no generate tests; so this is to help identify that
        '''
        dst_count = len(self.dsts) if isinstance(self.dsts, list) else 1
        test_count = len(self.tests)
        return test_count - dst_count

    def json(self):
        return dict(
            dsts=listify(self.dsts),
            srcs=listify(self.srcs),
            status=self.status,
            preserve_path=self.preserve_path,
            tests=listify(self.tests),
        )

    @property
    def server_name(self):
        return join([URL(src).netloc for src in self.srcs])

    def render(self):
        raise NotImplementedError
