#!/usr/bin/env python3

import os
import pytest

from refractr.generate import load_refractr, Refract
from refractr.validate import RefractrValidator

from leatherman.dictionary import head_body

NL_TAB = '\n  '
REFRACTR_YML = os.environ.get('REFRACTR_YML', 'refractr/refractr.yml')
LOCALHOST = '127.0.0.1'
LOCALHOST80 = f'{LOCALHOST}:80'

refractr = load_refractr(REFRACTR_YML)

@pytest.mark.parametrize('refract', refractr.refracts)
def test_refract(refract):
    print()
    print(refract)
    assert isinstance(refract, Refract)
    validator = RefractrValidator(netloc=LOCALHOST80, early=True)
    validator.validate_refract(refract)
