#!/usr/bin/env python3

import os
import pytest

from refractr import load_refractr, Refract, urlparse, replace
from utils import urlparse, validate_hop

from leatherman.dictionary import head_body

NL_TAB = '\n  '
LOCALHOST = '127.0.0.1'
REFRACTR_YML = os.environ.get('REFRACTR_YML', './refractr.yml')

refractr = load_refractr(REFRACTR_YML)

def validate_http_to_https(given, status):
    headers = {
        'Host': given.netloc
    }
    given1 = replace(given, netloc=LOCALHOST)
    expect = replace(given, scheme='https', path=given.path or '/')
    location = validate_hop(given1, expect, status, headers)
    return location

def validate_https_to_target(given, expect, status):
    headers = {
        'Host': given.netloc
    }
    given1 = replace(given, scheme='http', netloc=LOCALHOST+':443')
    location = validate_hop(given1, expect, status, headers)
    return location

def validate_redirect(src, dst, status):
    given = urlparse(src)
    expect = urlparse(dst)
    if given.scheme == 'http' and expect.scheme == 'https':
       given = validate_http_to_https(given, status)
    validate_https_to_target(given, expect, status)

@pytest.mark.parametrize('refract', refractr.refracts)
def test_refractr(refract):
    assert isinstance(refract, Refract)
    print(NL_TAB + NL_TAB.join(str(refract).split('\n')))
    for test in refract.tests:
        src, dst = head_body(test)
        validate_redirect(src, dst, refract.status)
