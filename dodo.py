#!/usr/bin/env python3

import os
import json

from doit.tools import LongRunning
from subprocess import check_output, CalledProcessError, PIPE

DIR = os.path.abspath(os.path.dirname(__file__))
CWD = os.path.abspath(os.getcwd())
REL = os.path.relpath(DIR, CWD)
REFRACTR = f'{DIR}/refractr'
NGINX = f'{REFRACTR}/nginx'
IMAGE = 'itsre/refractr'
REFRACTR_VERSION = check_output('git describe --match "v*" --abbrev=7', shell=True).decode('utf-8').strip()
CREDENTIALS_MESSAGE = 'Unable to locate credentials. You can configure credentials by running "aws configure".'
INGRESS_YAML_TEMPLATE = f'{DIR}/refractr-cd/ingress.yaml.template'

DOIT_CONFIG = {
    'default_tasks': ['test'],
    'verbosity': 2,
}


def call(cmd, stderr=PIPE, shell=True, **kwargs):
    result = check_output(
        cmd,
        stderr=stderr,
        shell=shell,
        **kwargs).decode('utf-8').strip()
    return result

def aws_account():
    cmd = 'aws sts get-caller-identity'
    try:
        result = call(cmd)
        obj = json.loads(result)
        return obj['Account']
    except CalledProcessError as cpe:
        if CREDENTIALS_MESSAGE in cpe.stderr.decode():
            return 'MISSING_CREDENTIALS'

def reponame():
    cmd = 'basename $(git rev-parse --show-toplevel)'
    result = call(cmd, cwd=DIR)
    return result

AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
AWS_ACCOUNT = os.environ.get('AWS_ACCOUNT', aws_account())
REPONAME = os.environ.get('REPONAME', reponame())
REPOURL = f'{AWS_ACCOUNT}.dkr.ecr.{AWS_REGION}.amazonaws.com/{REPONAME}'

def envs(sep=' ', **kwargs):
    envs = dict(
        REFRACTR_VERSION=REFRACTR_VERSION,
        AWS_REGION=AWS_REGION,
        AWS_ACCOUNT=AWS_ACCOUNT,
    )
    return sep.join(
        [f'{key}={value}' for key, value in sorted(dict(envs, **kwargs).items())]
    )

def check_creds():
    cmd = 'aws sts get-caller-identity'
    try:
        call(cmd)
        return True
    except CalledProcessError as cpe:
        if CREDENTIALS_MESSAGE in cpe.stderr.decode():
            return False
        raise cpe

def task_creds():
    '''
    verify the appropriate creds are present
    '''
    return {
        'actions': [
            f'echo "{CREDENTIALS_MESSAGE}"',
        ],
        'uptodate': [check_creds],
    }

def task_nginx():
    '''
    generate nginx.conf files from refractr.yml
    '''
    cmd = f'bin/refractr > {NGINX}/conf.d/refractr.conf'
    return {
        'actions': [
            cmd,
            f'echo "{cmd}"',
        ],
    }

def task_ingress():
    '''
    create ingress.yaml from refractr.yml domains and ingress.yaml.template
    '''
    cmd  = f'bin/refractr --ingress-template {INGRESS_YAML_TEMPLATE} > {INGRESS_YAML_TEMPLATE.replace(".template", "")}'
    return {
        'actions': [
            cmd,
            f'echo "{cmd}"',
        ],
    }

def task_build():
    '''
    run docker-compose build for refractr
    '''
    return {
        'task_dep': [
            'creds',
            'nginx',
        ],
        'actions': [
            f'env {envs()} docker-compose build',
            f'env {envs()} docker image prune -f --filter label=stage=intermediate',
        ],
    }

def task_check():
    '''
    run nginx -t test on refractr nginx config
    '''
    return {
        'task_dep': [
            'creds',
            'build',
        ],
        'actions': [
            f'env {envs()} docker-compose run refractr nginx -t',
        ],
    }

def task_drun():
    '''
    run refractr container via docker-compose up -d
    '''
    return {
        'task_dep': [
            'creds',
            'check',
        ],
        'actions': [
            # https://github.com/docker/compose/issues/1113#issuecomment-185466449
            f'env {envs()} docker-compose rm --force refractr',
            LongRunning(
                f'nohup env {envs()} docker-compose up -d --remove-orphans refractr >/dev/null &'),
        ],
    }

def task_test():
    '''
    run pytest tests against the locally running container
    '''
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

def task_login():
    '''
    perform ECR docker login via AWS perms
    '''
    cmd = f'aws ecr get-login-password --region {AWS_REGION} | docker login --username AWS --password-stdin {REPOURL}'
    return {
        'task_dep': [
            'creds',
        ],
        'actions': [
            cmd,
        ],
    }

def task_publish():
    '''
    publish docker image to aws ECR
    '''
    return {
        'task_dep': [
            'creds',
            'login',
        ],
        'actions': [
            f'env {envs()} docker-compose push refractr',
        ],
    }
