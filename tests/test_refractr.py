#!/usr/bin/env python3

import os
import pytest

from leatherman.dictionary import head_body
from leatherman.yaml import yaml_print

from refractr.utils import *
from refractr.base import BaseRefract
from refractr.refractr import Refractr
from refractr.validate import RefractrValidator, SUCCESS_RESULT

NL_TAB = '\n  '
REFRACTR_YML = os.getenv('REFRACTR_YML', 'refractr/refractr.yml')

refractr = Refractr(REFRACTR_YML, netloc='localhost', early=True, vebose=False)
validator = RefractrValidator(netloc='localhost', early=True, verbose=False)

@pytest.mark.parametrize('refract', refractr.refracts)
def test_refract(refract):
    print()
    print(refract)
    assert isinstance(refract, BaseRefract)
    validation = validator.validate_refract(refract)
    yaml_print(dict(validation=validation))
    assert validation['validate-result'] == SUCCESS_RESULT
