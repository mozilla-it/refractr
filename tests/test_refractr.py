#!/usr/bin/env python3

import os

import pytest
from leatherman.dictionary import head_body
from yaml import safe_dump

from refractr.base import BaseRefract
from refractr.cfg import CFG
from refractr.refractr import Refractr
from refractr.utils import *
from refractr.validate import SUCCESS_RESULT, RefractrValidator

NL_TAB = "\n  "

refractr = Refractr(CFG.REFRACTR_YML, netloc="localhost", early=True, vebose=False)
validator = RefractrValidator(netloc="localhost", early=True, verbose=False)


@pytest.mark.parametrize("refract", refractr.refracts)
def test_refract(refract):
    print()
    print(refract)
    assert isinstance(refract, BaseRefract)
    validation = validator.validate_refract(refract)
    print(safe_dump(dict(validation=validation)))
    assert validation["validate-result"] == SUCCESS_RESULT, validation
