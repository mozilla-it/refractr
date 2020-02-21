#!/usr/bin/env python3

from doit.tools import LongRunning
from subprocess import check_output

IMAGE = 'itsre/refractr'
CONTAINER = 'refractr-test'
VERSION = check_output('git describe --match "v*" --abbrev=7', shell=True).decode('utf-8').strip()

DOIT_CONFIG = {
    'default_tasks': ['test'],
    'verbosity': 2,
}

def task_nginx():
    return {
        'actions': [
            'bin/refractr > etc/nginx/conf.d/refractr.conf',
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
            'nginx',
        ],
        'actions': [
            f'docker build . -t {IMAGE}:{VERSION}',
        ],
    }

def task_check():
    return {
        'task_dep': [
            'build',
        ],
        'actions': [
            f'docker run {IMAGE}:{VERSION} nginx -t',
        ],
    }

def task_drun():
    return {
        'task_dep': [
            'check',
        ],
        'actions': [
            f'[ "$(docker ps -a | grep {CONTAINER})" ] && docker rm -f {CONTAINER} || true',
            LongRunning(
                f'nohup docker run -d -p 80:80 -p 443:443 --name {CONTAINER} {IMAGE}:{VERSION} > /dev/null &'),
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
            'PYTHONPATH=./src python3 -m pytest -vv -q -s',
        ],
    }
