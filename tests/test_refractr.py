#!/usr/bin/env python3

import os
import pytest

from leatherman.dictionary import head_body
from leatherman.yaml import yaml_print

from refractr.utils import *
from refractr.base import BaseRefract
from refractr.refractr import Refractr
from refractr.validate import RefractrValidator

NL_TAB = '\n  '
REFRACTR_YML = os.environ.get('REFRACTR_YML', 'refractr/refractr.yml')
LOCALHOST = '127.0.0.1'
LOCALHOST80 = f'{LOCALHOST}:80'

refractr = Refractr(REFRACTR_YML, netloc='localhost', early=True, vebose=False)

@pytest.mark.parametrize('refract', refractr.refracts)
def test_refract(refract):
    print()
    print(refract)
    assert isinstance(refract, BaseRefract)
    validator = RefractrValidator(netloc='localhost', early=True, verbose=False)
    validation = validator.validate_refract(refract)
    assert validation['validate-result'] == 'SUCCESS'
    yaml_print(dict(validation=validation))
