#!/usr/bin/env python3

import os
import re
import sys
import requests

from urllib.parse import ParseResult

from refractr.utils import *
from leatherman.dictionary import head_body
from leatherman.dbg import dbg


# makes visualizing as string easier to read
ParseResult.__repr__ = lambda self: self.geturl()

def replace(pr, **kwargs):
    return ParseResult(
        scheme=kwargs.get('scheme', pr.scheme),
        netloc=kwargs.get('netloc', pr.netloc),
        path=kwargs.get('path', pr.path),
        params=kwargs.get('params', pr.params),
        query=kwargs.get('query', pr.query),
        fragment=kwargs.get('fragment', pr.fragment))

class Hop:
    def __init__(self, src, dst=None, status=None, match=None, ex=None):
        self.src = src
        self.dst = dst
        self.status = status
        self.match = match
        self.ex = ex

    def __str__(self):
        if isinstance(self.ex, Exception):
            return f'{self.src} => {self.ex.__class__.__name__}'
        return f'{self.status} {self.src} -> {self.dst}' + (f' {self.match}' if self.match else '')


class RefractrValidator:
    def __init__(self, early=False, netloc=None, verbose=False):
        self.early = early
        self.netloc = netloc
        self.verbose = verbose
        if netloc:
            self.verify = False
            requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        else:
            self.verify = True
            requests.packages.urllib3.warnings.resetwarnings()

    def hop(self, src, netloc, **kwargs):
        headers = kwargs.get('headers', {})
        if netloc:
            headers.update(Host=src.netloc)
            src = replace(src, netloc=netloc)
        response = requests.get(
            src.geturl(),
            headers=headers,
            allow_redirects=False,
            verify=self.verify)
        dst = response.headers.get('Location', None)
        if dst:
            dst = urlparse(dst)
            if dst.netloc == '':
                dst = replace(dst, netloc=src.netloc)
        return dst, response.status_code

    def follow_hops(self, given_src, expect_dst, expect_status):
        netloc = self.netloc
        src = given_src
        result = None
        hops = []
        while src:
            dst = None
            try:
                dst, status = self.hop(src, netloc)
            except Exception as ex:
                hop = Hop(src, ex=ex)
                hops += [hop]
                break
            if dst:
                match = None
                if dst == expect_dst:
                    if status == expect_status:
                        match = 'MATCHED'
                    else:
                        match = 'STATUS!'
                hop = Hop(src, dst, status, match)
                hops += [hop]
                if match:
                    result = match
                if match == 'MATCHED':
                    # bail early if we have met our expectation
                    if self.early:
                        break
                    # we can't do netloc override outside of our refractr nginx
                    netloc = None
                src = dst
                continue
            break
        return hops, result

    def validate_refract(self, refract):
        tests = []
        for test in refract.tests:
            src, dst = head_body(test)
            hops, result = self.follow_hops(urlparse(src), urlparse(dst), refract.status)
            tests += [{f'{src} -> {dst}': dict(
                hops=[
                    str(hop)
                    for hop
                    in hops
                ],
                result=result,
            )}]
        return dict(netloc=self.netloc or 'public', tests=tests)

    def validate(self, refractr):
        for refract in refractr.refracts:
            results = self.validate_refract(refract)
            refract.results = results
        return refractr
