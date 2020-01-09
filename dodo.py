#!/usr/bin/env python3

from doit.tools import LongRunning

IMAGE = 'refractr'
CONTAINER = 'refractr-test'

DOIT_CONFIG = {
    'verbosity': 2,
}

def task_generate():
    return {
        'actions': [
            'bin/refractr > etc/nginx/conf.d/refractr.conf',
        ],
    }

def task_build():
    return {
        'task_dep': [
            'generate',
        ],
        'actions': [
            f'docker build . -t {IMAGE}',
        ],
    }

def task_drun():
    return {
        'task_dep': [
            'build',
        ],
        'actions': [
                f'[ "$(docker ps | grep {CONTAINER})" ] && docker rm -f {CONTAINER} || true',
            LongRunning(
                f'nohup docker run -d -p 80:80 -p 443:443 --name {CONTAINER} {IMAGE}  > /dev/null &'),
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
            f'docker exec {CONTAINER} nginx -t',
            'PYTHONPATH=./src python3 -m pytest -vv -q',
        ],
    }
