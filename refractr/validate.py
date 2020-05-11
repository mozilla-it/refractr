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

    def follow_hops(self, given_src, expect_dst):
        results = []
        netloc = self.netloc
        src = given_src
        while src:
            dst, status = self.hop(src, netloc)
            if dst:
                if self.verbose:
                    print(f'  {netloc or "public"} | {status} {src} -> {dst}')
                matched = dst == expect_dst
                result = (src, dst, status, matched)
                results += [result]
                if matched:
                    # bail early if we have met our expectation
                    if self.early:
                        break
                    # we can't do netloc override outside of our refractr nginx
                    netloc = None
                src = dst
                continue
            break
        return results

    def validate_test(self, given_src, expect_dst, expect_status):
        if self.verbose:
            print(f'validate: {given_src} -> {expect_dst} => {expect_status}')
        results = self.follow_hops(given_src, expect_dst)
        assert results, '!hops {given_src} -> {expect_dst} => {expect_status}'
        for src, dst, status, match_ in reversed(results):
            if match_:
                assert status == expect_status, f'{src} -> {dst} | {status} != {expect_status}'
                return
        assert results[-1][1] == expect_dst, f'{results[-1][1]} != {expect_dst}'

    def validate_refract(self, refract):
        if self.verbose:
            print(refract, end='\n\n')
        for test in refract.tests:
            src, dst = head_body(test)
            self.validate_test(urlparse(src), urlparse(dst), refract.status)

    def validate(self, refractr):
        for refract in refractr.refracts:
            self.validate_refract(refract)
