#!/usr/bin/env python3

import os
import re
import sys
sys.dont_write_bytecode = True

def validate_hop(given, expect, headers, status):
    response = requests.get(given.geturl(), headers=headers, allow_redirects=False)
    assert response.status_code == status
    location = urlparse(response.headers['Location'])
    assert location == expect
    return location
