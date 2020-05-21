#!/usr/bin/env python3

import os
import re
import json

from doit.tools import LongRunning
from subprocess import check_output, CalledProcessError, PIPE
from ruamel.yaml import safe_load
from jsonschema import validate
from jsonschema.exceptions import ValidationError

DIR = os.path.abspath(os.path.dirname(__file__))
CWD = os.path.abspath(os.getcwd())
REL = os.path.relpath(DIR, CWD)
REFRACTR = f'{REL}/refractr'
REFRACTR_YML = f'{REFRACTR}/refractr.yml'
SCHEMA_YML = f'{REFRACTR}/schema.yml'
NGINX = f'{REFRACTR}/nginx'
IMAGE = 'itsre/refractr'
CREDENTIALS_MESSAGE = 'Unable to locate credentials. You can configure credentials by running "aws configure".'
INGRESS_YAML_TEMPLATE = f'{REFRACTR}/ingress.yaml.template'
PROD_TAG_PN = '$(v[0-9]+.[0-9]+.[0-9]+)$'
TRAVIS = os.getenv('TRAVIS')
TRAVIS_TAG = os.getenv('TRAVIS_TAG')
TRAVIS_BRANCH = os.getenv('TRAVIS_BRANCH')
TRAVIS_PULL_REQUEST = os.getenv('TRAVIS_PULL_REQUEST')
PUBLISH_BRANCHES = [
    'master',
]

DOIT_CONFIG = {
    'default_tasks': ['test'],
    'verbosity': 2,
}

def call(cmd, stderr=PIPE, shell=True, **kwargs):
    result = check_output(
        cmd,
        stderr=stderr,
        shell=shell,
        **kwargs).decode('utf-8').rstrip()
    return result

def branch_contains(tag, approved):
    '''
    determine if tag points to ref on one of approved branches
    '''
    cmd = f'git branch --contains "{tag}"'
    try:
        lines = call(cmd).split('\n')
        branches = [line[2:] for line in lines]
        return not set(branches).isdisjoint(approved)
    except CalledProcessError as cpe:
        return False

def aws_account():
    cmd = 'aws sts get-caller-identity'
    result = call(cmd)
    obj = json.loads(result)
    return obj['Account']

def reponame():
    cmd = 'basename $(git rev-parse --show-toplevel)'
    result = call(cmd, cwd=REL)
    return result

AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')
AWS_ACCOUNT = os.getenv('AWS_ACCOUNT', aws_account())
REPONAME = os.getenv('REPONAME', reponame())
REPOURL = f'{AWS_ACCOUNT}.dkr.ecr.{AWS_REGION}.amazonaws.com/{REPONAME}'
REFRACTR_VERSION = call('git describe --match "v*" --abbrev=7')

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

def task_schema():
    '''
    test refractr.yml against schema.yml using jsonschema
    '''
    def schema():
        assert os.path.isfile(REFRACTR_YML)
        assert os.path.isfile(SCHEMA_YML)
        print(f'validating {REFRACTR_YML} against {SCHEMA_YML} =>', end=' ')
        with open(REFRACTR_YML, 'r') as f:
            refractr_yml = safe_load(f)
        with open(SCHEMA_YML, 'r') as f:
            schema_yml = safe_load(f)
        try:
            validate(refractr_yml, schema_yml)
            print('SUCCESS')
            return True
        except ValidationError as ve:
            print('FAILURE')
            print(ve)
            return False
    return {
        'task_dep': [
        ],
        'actions': [
            schema,
        ]
    }

def task_nginx():
    '''
    generate nginx.conf files from refractr.yml
    '''
    cmd = f'bin/refractr nginx > {NGINX}/conf.d/refractr.conf'
    return {
        'task_dep': [
            'schema',
        ],
        'actions': [
            cmd,
            f'echo "{cmd}"',
        ],
    }

def task_ingress():
    '''
    create ingress.yaml from refractr.yml domains and ingress.yaml.template
    '''
    cmd = f'bin/refractr ingress --ingress-template {INGRESS_YAML_TEMPLATE} > {INGRESS_YAML_TEMPLATE.replace(".template", "")}'
    return {
        'task_dep': [
            'schema',
        ],
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
            'ingress',
        ],
        'actions': [
            f'env {envs()} docker-compose build refractr',
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
            f'env {envs()} docker-compose run refractr check',
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
            'PYTHONPATH=. python3 -m pytest -vv -q -s',
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
    def should_publish():
        publish = False
        print(' '.join([
            f'TRAVIS={TRAVIS}',
            f'TRAVIS_TAG={TRAVIS_TAG}',
            f'TRAVIS_BRANCH={TRAVIS_BRANCH}',
            f'TRAVIS_PULL_REQUEST={TRAVIS_PULL_REQUEST}',
            f'branch_contains={branch_contains(TRAVIS_TAG, PUBLISH_BRANCHES)}',
        ]))
        if TRAVIS:
            if TRAVIS_PULL_REQUEST == "false":
                if TRAVIS_TAG and branch_contains(TRAVIS_TAG, PUBLISH_BRANCHES):
                    publish = True
                elif TRAVIS_BRANCH and TRAVIS_BRANCH in PUBLISH_BRANCHES:
                    publish = True
        elif not re.search(PROD_TAG_PN, REFRACTR_VERSION):
            publish = True
        print(f'publishing {REFRACTR_VERSION if publish else "skipped"}')
        return publish

    return {
        'task_dep': [
            'test',
            'creds',
            'login',
        ],
        'actions': [
            f'env {envs()} docker-compose push refractr',
        ],
        # inverse to tell doit task not uptodate, therefore publish
        'uptodate': [lambda: not should_publish()],
    }
