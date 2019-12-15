#!/usr/bin/env python3

from enum import Enum

def tuple_setter(value):
    if isinstance(value, (list, tuple)):
        return tuple(value)
    else:
        return (value,)


class Kind(Enum):
    REDIRECT = 1
    REWRITE = 2


class Refractr(object):

    @staticmethod
    def from_dict()

    def __init__(self, dst, src, kind=Kind.REDIRECT, status=307):
        self.dsts = dst
        self.srcs = src
        self.kind = kind
        self.status = status

    @property
    def dsts(self):
        return self._dsts

    @dsts.setter
    def dsts(self, value):
        self._dsts = tuple_setter(value)

    @property
    def srcs(self):
        return self._srcs

    @srcs.setter
    def srcs(self, value):
        self._srcs = tuple_setter(value)

    def __repr__(self):
        fields = ', '.join([
            f'dsts={self.dsts}',
            f'srcs={self.srcs}',
            f'kind={self.kind}',
            f'satus={self.status}',
        ])
        return f'{self.__class__.__name__}({fields})'
