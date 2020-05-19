#!/usr/bin/env python3

import os
import re
import sys
import aiohttp
import asyncio
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
        self._loop = asyncio.get_event_loop()
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

    async def _hop(self, src, netloc):
        headers = {}
        if netloc:
            headers.update(Host=URL(src).netloc)
            src = URL(src, netloc=netloc).http # force to http for non-prod

        ctor = aiohttp.TCPConnector(verify_ssl=self.verify)
        async with aiohttp.ClientSession(connector=ctor, loop=self._loop) as session:
            async with session.request('GET', src, headers=headers, allow_redirects=False) as response:
                headers = response.headers
                dst = headers.get('Location', None)
                if dst and URL(dst).netloc == '':
                    dst = URL(dst, netloc=URL(src).netloc).url
                return dst, response.status

    async def _follow_hops(self, name, given_src, expect_dst, expect_status):
        netloc = self.netloc
        src = given_src
        test_result = 'MISMATCHED'
        hops = []
        while src:
            dst = None
            try:
                dst, status = await self._hop(src, netloc)
            except Exception as ex:
                hop = Hop(src, ex=ex)
                test_result = hop.match
                hops += [hop]
                break
            if dst:
                if src == dst:
                    hop = Hop(src)
                    test_result = 'InfiniteLoop'
                    hops += [hop]
                    break
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
        return name, hops, test_result

    async def _validate_refract(self, refract):
        futures = []
        for test in refract.tests:
            src, dst = head_body(test)
            name = f'{src} -> {dst}'
            futures += [
                asyncio.ensure_future(
                    self._follow_hops(name, src, dst, refract.status))
            ]
        results = await asyncio.gather(*futures)
        validate_result = 'SUCCESS'
        tests = []
        for name, hops, test_result in results:
            if test_result != 'MATCHED':
                validate_success = 'FAILURE'
            tests += [{
                name: {
                    'hops': [str(hop) for hop in hops],
                    'test-result': test_result,
                }
            }]
        return refract, tests

    def validate_refract(self, refract):
        return self._loop.run_until_complete(self._validate_refract(refract))

    async def _validate_refracts(self, refracts):
        futures = [
            asyncio.ensure_future(self._validate_refract(refract))
            for refract in refracts
        ]
        results = await asyncio.gather(*futures)
        validated = []
        for refract, validation in results:
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
