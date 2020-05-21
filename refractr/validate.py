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
            src = URL(src, netloc=netloc).http # force to http for non-prod
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
        test_result = 'MISMATCHED'
        hops = []
        while src:
            dst = None
            try:
                dst, status, reason = await self._hop(src, netloc)
            except Exception as ex:
                hop = Hop(src, ex=ex)
                test_result = hop.match
                hops += [hop]
                break
            if status > 400:
                test_result = reason
                break
            if dst:
                if src == dst:
                    hop = Hop(src)
                    test_result = 'InfiniteLoop'
                    hops += [hop]
                    break
                match = None
                if dst == expect_dst:
                    if expect_status == None:
                        test_result = 'ExpectStatusNotSpecified'
                        break
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

    async def _validate_refract(self, refract):
        validate_result = 'SUCCESS'
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
        for name, (hops, test_result) in zip(names, results):
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
