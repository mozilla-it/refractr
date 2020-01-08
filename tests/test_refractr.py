#!/usr/bin/env python3

import os
import pytest
import requests
from urllib.parse import ParseResult

from refractr import load_refractr, Refract, urlparse

from leatherman.dbg import dbg

REFRACTR_YML = os.environ.get('REFRACTR_YML', './refractr.yml')

refractr = load_refractr(REFRACTR_YML)

def _test_redirect(src, dst, status, localhost='127.0.0.1'):
    given = urlparse(src)
    expect = urlparse(dst)
    headers = {
        'Host': given.netloc
    }
    if given.scheme == 'http': # and expect.scheme == 'https':
        given1 = ParseResult(
            scheme=given.scheme,
            netloc=localhost,
            path=given.path,
            params=given.params,
            query=given.query,
            fragment=given.fragment)
        expect1 = ParseResult(
            scheme='https',
            netloc=given.netloc,
            path=given.path or '/', # ensure trailing /
            params=given.params,
            query=given.query,
            fragment=given.fragment)
        r1 = requests.get(given1.geturl(), headers=headers, allow_redirects=False)
        assert r1.status_code == status
        location = urlparse(r1.headers['Location'])
        dbg(given)
        dbg(expect1)
        dbg(location)
        assert location == expect1

@pytest.mark.parametrize('refract', refractr.refracts)
def test_refractr(refract):
    assert isinstance(refract, Refract)
    assert refract.tests
    for src, dst in refract.tests.items():
        _test_redirect(src, dst, refract.status)
