#!/usr/bin/env python3

import os
import pytest
import requests
from urllib.parse import ParseResult

from refractr import load_refractr, Refract, urlparse

from leatherman.dbg import dbg

NL_TAB = '\n  '
LOCALHOST = '127.0.0.1'
REFRACTR_YML = os.environ.get('REFRACTR_YML', './refractr.yml')

refractr = load_refractr(REFRACTR_YML)

def replace(pr, **kwargs):
    return ParseResult(
        scheme=kwargs.get('scheme', pr.scheme),
        netloc=kwargs.get('netloc', pr.netloc),
        path=kwargs.get('path', pr.path),
        params=kwargs.get('params', pr.params),
        query=kwargs.get('query', pr.query),
        fragment=kwargs.get('fragment', pr.fragment))

def _validate_hop(given, expect, headers, status):
    response = requests.get(given.geturl(), headers=headers, allow_redirects=False)
    assert response.status_code == status
    location = urlparse(response.headers['Location'])
    assert location == expect
    return location

def _test_http_to_https(given, status):
    headers = {
        'Host': given.netloc
    }
    given1 = replace(given, netloc=LOCALHOST)
    expect = replace(given, scheme='https', path=given.path or '/')
    location = _validate_hop(given1, expect, headers, status)
    return location

def _test_https_to_target(given, expect, status):
    headers = {
        'Host': given.netloc
    }
    given1 = replace(given, scheme='http', netloc=LOCALHOST+':443')
    location = _validate_hop(given1, expect, headers, status)
    return location

def _test_redirect(src, dst, status):
    given = urlparse(src)
    expect = urlparse(dst)
    if given.scheme == 'http' and expect.scheme == 'https':
       given = _test_http_to_https(given, status)
    _test_https_to_target(given, expect, status)

@pytest.mark.parametrize('refract', refractr.refracts)
def test_refractr(refract):
    assert isinstance(refract, Refract)
    assert refract.tests
    print(NL_TAB+NL_TAB.join(str(refract).split('\n')))
    for src, dst in refract.tests.items():
        _test_redirect(src, dst, refract.status)
