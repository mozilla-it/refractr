#!/usr/bin/env python3

import os

from doit.tools import LongRunning
from subprocess import check_output

DIR = os.path.abspath(os.path.dirname(__file__))
CWD = os.path.abspath(os.getcwd())
REL = os.path.relpath(DIR, CWD)
REFRACTR = f'{DIR}/refractr'
NGINX = f'{REFRACTR}/nginx'
IMAGE = 'itsre/refractr'
REFRACTR_VERSION = check_output('git describe --match "v*" --abbrev=7', shell=True).decode('utf-8').strip()

DOIT_CONFIG = {
    'default_tasks': ['test'],
    'verbosity': 2,
}

def envs(sep=' ', **kwargs):
    envs = dict(
        REFRACTR_VERSION=REFRACTR_VERSION
    )
    return sep.join(
        [f'{key}={value}' for key, value in sorted(dict(envs, **kwargs).items())]
    )

def task_generate():
    return {
        'actions': [
            f'bin/refractr > {NGINX}/conf.d/refractr.conf',
        ],
    }

def task_domains():
    return {
        'actions': [
            'bin/refractr --domains-only > domains.yml',
        ]
    }

def task_build():
    return {
        'task_dep': [
            'generate',
        ],
        'actions': [
            f'env {envs()} docker-compose build'
        ],
    }

def task_check():
    return {
        'task_dep': [
            'build',
        ],
        'actions': [
            f'docker run {IMAGE}:{REFRACTR_VERSION} nginx -t',
        ],
    }

def task_drun():
    return {
        'task_dep': [
            'check',
        ],
        'actions': [
            LongRunning(
                f'nohup env {envs()} docker-compose up -d --force-recreate >/dev/null &'),
        ],
    }

def task_test():
    return {
        'task_dep': [
            'build',
            'drun',
        ],
        'actions': [
            'sleep 1',
            'PYTHONPATH=./refractr python3 -m pytest -vv -q -s',
        ],
    }
