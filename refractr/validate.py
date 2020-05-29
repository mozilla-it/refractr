#!/usr/bin/env python3

import os
import re
import sys
import aiohttp
import asyncio

from refractr.exceptions import InsufficientAmountOfTestsError
from refractr.utils import *
from refractr.url import URL
from leatherman.dictionary import head_body
from leatherman.repr import __repr__
from leatherman.dbg import dbg

LOOP_RESULT = 'LOOP!'
STATUS_RESULT = 'STATUS!'
MATCHED_RESULT = 'MATCHED'
MISMATCH_RESULT = 'MISMATCH'
SUCCESS_RESULT = 'SUCCESS'
FAILURE_RESULT = 'FAILURE'

class Hop:
    def __init__(self, test, src, dst=None, status=None, ex=None):
        assert isinstance(test, Test)
        self.test = test #ref to test instance
        self.src = src
        self.dst = dst
        self.status = status
        self.ex = ex

    __repr__ = __repr__

    def __str__(self):
        result = self.result or ''
        if isinstance(self.ex, Exception):
            return f'{self.src} => {result}'
        return f'{self.status} {self.src} -> {self.dst} {result}'.rstrip()

    @property
    def result(self):
        if self.ex:
            return self.ex.__class__.__name__
        elif self.src == self.dst:
            return LOOP_RESULT
        elif self.dst and self.dst == self.test.expect_dst:
            if self.status and self.status == self.test.expect_status:
                return MATCHED_RESULT
            return STATUS_RESULT
        return None

class Test:
    def __init__(self, expect_dst, expect_status):
        self.expect_dst = expect_dst
        self.expect_status = expect_status
        self.hops = []
        self._result = None

    __repr__ = __repr__

    @property
    def result(self):
        return self._result or MISMATCH_RESULT

    def add_hop(self, src, dst=None, status=None, ex=None):
        hop = Hop(self, src, dst, status, ex)
        if hop.result == LOOP_RESULT:
            self._result = LOOP_RESULT
        if self._result == None:
            self._result = hop.result
        self.hops += [hop]

class RefractrValidator:
    def __init__(self, netloc=None, early=False, verbose=False):
        self._loop = asyncio.get_event_loop()
        self.netloc = netloc
        self.early = early
        self.verbose = verbose
        # only verify ssl on prod, not stage or localhost
        self.ssl = False if netloc else True

    __repr__ = __repr__

    async def _hop(self, src, netloc):
        headers = {}
        if netloc:
            headers.update(Host=URL(src).netloc)
            src = URL(src, netloc=netloc).url
            # force to http for localhost
            if netloc == 'localhost':
                src = URL(src).http
        ctor = aiohttp.TCPConnector(ssl=self.ssl)
        async with aiohttp.ClientSession(connector=ctor, loop=self._loop) as session:
            async with session.request('GET', src, headers=headers, allow_redirects=False) as response:
                headers = response.headers
                dst = headers.get('Location', None)
                if dst and URL(dst).netloc == '':
                    dst = URL(dst, netloc=URL(src).netloc).url
                return dst, response.status, response.reason

    async def _follow_hops(self, given_src, expect_dst, expect_status):
        netloc = self.netloc
        src = given_src
        hops = []
        if expect_status == None:
            test_result = 'ExpectStatusNotSpecified'
            return hops, test_result
        test = Test(expect_dst, expect_status)
        while src:
            dst = None
            try:
                dst, status, reason = await self._hop(src, netloc)
            except Exception as ex:
                test.add_hop(src, ex=ex)
                break
            if status >= 400:
                test.add_hop(src, dst, status)
                break
            if dst:
                test.add_hop(src, dst, status)
                if test.result == LOOP_RESULT:
                    break
                if test.result == MATCHED_RESULT:
                    if self.early:
                        break
                    # we can't do netloc override outside of our refractr nginx
                    netloc = None
                src = dst
                continue
            break
        return test

    async def _validate_refract(self, refract):
        validate_result = SUCCESS_RESULT
        names = []
        futures = []
        if refract.balance < 0:
            raise InsufficientAmountOfTestsError(refract.balance)
        for test in refract.tests:
            status = test.pop('status', refract.status)
            src, dst = head_body(test)
            names += [
                f'{src} -> {dst}'
            ]
            futures += [
                asyncio.ensure_future(
                    self._follow_hops(src, dst, status))
            ]
        results = await asyncio.gather(*futures)
        tests = []
        for name, test in zip(names, results):
            if test.result != MATCHED_RESULT:
                validate_result = FAILURE_RESULT
            tests += [{
                name: {
                    'hops': [str(hop) for hop in test.hops],
                    'test-result': test.result,
                }
            }]
        return {
            'netloc': self.netloc or 'public',
            'tests': tests,
            'validate-result': validate_result,
        }

    def validate_refract(self, refract):
        return self._loop.run_until_complete(self._validate_refract(refract))

    async def _validate_refracts(self, refracts):
        futures = [
            asyncio.ensure_future(self._validate_refract(refract))
            for refract in refracts
        ]
        results = await asyncio.gather(*futures)
        validated = []
        for refract, validation in zip(refracts, results):
            json = refract.json()
            json.pop('tests')
            json['validation'] = validation
            validated += [json]
        return {
            'refracts': validated,
            'refracts-count': len(validated),
        }

    def validate_refracts(self, refracts):
        return self._loop.run_until_complete(self._validate_refracts(refracts))
