#!/usr/bin/env python3

import os
import re
import sys
import requests
import warnings

from refractr.utils import *
from refractr.url import URL
from leatherman.dictionary import head_body
from leatherman.repr import __repr__
from leatherman.dbg import dbg

class Hop:
    def __init__(self, src, dst=None, status=None, match=None, ex=None):
        self.src = src
        self.dst = dst
        self.status = status
        self._match = match
        self.ex = ex

    __repr__ = __repr__

    @property
    def match(self):
        if self.ex:
            return self.ex.__class__.__name__
        return self._match if self._match else ''

    def __str__(self):
        if isinstance(self.ex, Exception):
            return f'{self.src} => {self.match}'
        return f'{self.status} {self.src} -> {self.dst} {self.match}'.rstrip()


class RefractrValidator:
    def __init__(self, netloc=None, early=False, verbose=False):
        self.netloc = netloc
        self.early = early
        self.verbose = verbose
        if netloc:
            self.verify = False
            requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        else:
            self.verify = True
            requests.packages.urllib3.warnings.resetwarnings()

    __repr__ = __repr__

    def hop(self, src, netloc, **kwargs):
        headers = kwargs.get('headers', {})
        if netloc:
            headers.update(Host=URL(src).netloc)
            src = URL(src, netloc=netloc).http # force to http for non-prod
        response = requests.get(
            src,
            headers=headers,
            allow_redirects=False,
            verify=self.verify)
        dst = response.headers.get('Location', None)
        if dst and URL(dst).netloc == '':
            dst = URL(dst, netloc=URL(src).netloc).url
        return dst, response.status_code

    def follow_hops(self, given_src, expect_dst, expect_status):
        netloc = self.netloc
        src = given_src
        test_result = 'MISMATCHED'
        hops = []
        while src:
            dst = None
            try:
                dst, status = self.hop(src, netloc)
            except Exception as ex:
                hop = Hop(src, ex=ex)
                test_result = hop.match
                hops += [hop]
                break
            if dst:
                assert src != dst, f'after hop: dst={dst} should not be src={src}; infinite loop!'
                match = None
                if dst == expect_dst:
                    if status == expect_status:
                        match = 'MATCHED'
                    else:
                        match = 'STATUS!'
                hop = Hop(src, dst, status, match)
                hops += [hop]
                if match:
                    test_result = match
                if match == 'MATCHED':
                    # bail early if we have met our expectation
                    if self.early:
                        break
                    # we can't do netloc override outside of our refractr nginx
                    netloc = None
                src = dst
                continue
            break
        return hops, test_result

    def validate_refract(self, refract):
        validate_result = 'SUCCESS'
        tests = []
        for test in refract.tests:
            src, dst = head_body(test)
            name = f'{src} -> {dst}'
            hops, test_result = self.follow_hops(src, dst, refract.status)
            if test_result != 'MATCHED':
                validate_result = 'FAILURE'
            tests += [{
                name: {
                    'hops': [str(hop) for hop in hops],
                    'test-result': test_result,
                }
            }]
        return {
            'netloc': self.netloc or 'public',
            'tests': tests,
            'validate-result': validate_result
        }

    def validate_refracts(self, refracts):
        validated = []
        for refract in refracts:
            validation = self.validate_refract(refract)
            json = refract.json()
            json.pop('tests')
            json['validation']=validation
            validated += [json]
        return {
            'refracts': validated,
            'refracts-count': len(validated),
        }
