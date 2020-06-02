# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import re
import json

from datetime import datetime
from functools import lru_cache
from decouple import UndefinedValueError, AutoConfig, config
from subprocess import Popen, CalledProcessError, PIPE  # nosec

DIR = os.path.abspath(os.path.dirname(__file__))
CWD = os.path.abspath(os.getcwd())
REL = os.path.relpath(DIR, CWD)

CREDENTIALS_MESSAGE = 'Unable to locate credentials. You can configure credentials by running "aws configure".'

class NotGitRepoError(Exception):
    def __init__(self, cwd=os.getcwd()):
        msg = f"not a git repository error cwd={cwd}"
        super().__init__(msg)


class GitCommandNotFoundError(Exception):
    def __init__(self):
        msg = "git: command not found"
        super().__init__(msg)

def call(
    cmd,
    stdout=PIPE,
    stderr=PIPE,
    shell=True,
    nerf=False,
    throw=True,
    verbose=False):

    if nerf:
        return (None, "nerfed", "nerfed")
    process = Popen(cmd, stdout=stdout, stderr=stderr, shell=shell)  # nosec
    _stdout, _stderr = [
        stream.decode("utf-8") if stream is not None else None
        for stream in process.communicate()
    ]
    exitcode = process.poll()
    if throw and exitcode:
        raise CalledProcessError(
            exitcode, f"cmd={cmd}; stdout={_stdout}; stderr={_stderr}"
        )
    return exitcode, _stdout, _stderr

def git(args, strip=True, **kwargs):
    try:
        _, stdout, stderr = call("git rev-parse --is-inside-work-tree")
    except CalledProcessError as ex:
        if "not a git repository" in str(ex):
            raise NotGitRepoError
        elif "git: command not found" in str(ex):
            raise GitCommandNotFoundError
    try:
        _, result, _ = call(f"git {args}", **kwargs)
        if result:
            result = result.strip()
        return result
    except CalledProcessError as ex:
        raise ex


class AutoConfigPlus(AutoConfig):  # pylint: disable=too-many-public-methods

    @property
    def IS_AUTHORIZED(self):
        try:
            call('aws sts get-caller-identity')
        except CalledProcessError as cpe:
            if CREDENTIALS_MESSAGE in cpe.stderr.decode():
                return False
            raise cpe

    @property
    @lru_cache()
    def REPONAME(self):
        result = git('rev-parse --show-toplevel')
        reponame = os.path.basename(result)
        return self('REPONAME', reponame)

    @property
    @lru_cache()
    def AWS_ACCOUNT(self):
        _, stdout, _ = call('aws sts get-caller-identity')
        obj = json.loads(stdout)
        return obj['Account']

    @property
    @lru_cache()
    def AWS_REGION(self):
        return self('AWS_REGION', 'us-west-2')

    @property
    @lru_cache()
    def ECR_REPOURL(self):
        ecr_repourl = f'{self.AWS_ACCOUNT}.dkr.ecr.{self.AWS_REGION}.amazonaws.com/{self.REPONAME}'
        return self('ECR_REPOURL', ecr_repourl)

    @property
    @lru_cache()
    def IMAGE_NAME_AND_TAG(self):
        return self('IMAGE_NAME_AND_TAG', f'{self.ECR_REPOURL}:{self.VERSION}')

    @property
    @lru_cache()
    def TRAVIS(self):
        return self('TRAVIS', False)

    @property
    @lru_cache()
    def TRAVIS_TAG(self):
        return self('TRAVIS_TAG')

    @property
    @lru_cache()
    def TRAVIS_BRANCH(self):
        return self('TRAVIS_BRANCH')

    @property
    @lru_cache()
    def TRAVIS_PULL_REQUEST(self):
        return self('TRAVIS_PULL_REQUEST')

    @property
    @lru_cache()
    def REFRACTR(self):
        return self('REFRACTR', REL)

    @property
    @lru_cache()
    def REFRACTR_YML(self):
        return self('REFRACTR_YML', f'{self.REFRACTR}/refractr.yml')

    @property
    @lru_cache()
    def SCHEMA_YML(self):
        return self('SCHEMA_YML', f'{self.REFRACTR}/schema.yml')

    @property
    @lru_cache()
    def INGRESS_YAML_TEMPLATE(self):
        return self('INGRESS_YAML_TEMPLATE', f'{self.REFRACTR}/ingress.yaml.template')

    @property
    @lru_cache()
    def IMAGE(self):
        return self('IMAGE', f'{self.REFRACTR}/image')

    @property
    @lru_cache()
    def NGINX(self):
        return self('NGINX', f'{self.REFRACTR}/nginx')

    @property
    @lru_cache()
    def VERSION(self):
        try:
            return git("describe --abbrev=7 --always")
        except (NotGitRepoError, GitCommandNotFoundError):
            return self("VERSION")

    @property
    @lru_cache()
    def BRANCH(self):
        try:
            return git("rev-parse --abbrev-ref HEAD")
        except (NotGitRepoError, GitCommandNotFoundError):
            return self("BRANCH")

    @property
    @lru_cache()
    def PUBLISH_BRANCHES(self):
        branches = self('PUBLISH_BRANCHES', None)
        if branches:
            return branches.split(',')
        return ['master']

    @property
    @lru_cache()
    def SHOULD_PUBLISH(self):
        publish = False
        if self.TRAVIS:
            if self.TRAVIS_PULL_REQUEST == "false":
                if self.TRAVIS_TAG and branch_contains(self.TRAVIS_TAG, self.PUBLISH_BRANCHES):
                    publish = True
                elif self.TRAVIS_BRANCH and self.TRAVIS_BRANCH in self.PUBLISH_BRANCHES:
                    publish = True
        elif not re.search(self.PROD_TAG_PATTERN, self.VERSION):
            publish = True
        return publish

    @property
    @lru_cache()
    def PROD_TAG_PATTERN(self):
        return self('PROD_TAG_PATTERN', '^(v[0-9]+\.[0-9]+\.[0-9]+)$')

    @property
    @lru_cache()
    def DEPLOYED_ENV(self):
        if self.TRAVIS:
            match = re.search(self.PROD_TAG_PATTERN, self.VERSION)
            if match:
                return 'prod'
            else:
                return 'stage'
        return 'dev'

    @property
    @lru_cache()
    def AUTHOR_NAME(self):
        author_name = git(f'log -1 {self.REVISION} --pretty="%aN"')
        return self('AUTHOR_NAME', author_name)

    @property
    @lru_cache()
    def AUTHOR_EMAIL(self):
        author_email = git(f'log -1 {self.REVISION} --pretty="%aE"')
        return self('AUTHOR_EMAIL', author_email)

    @property
    @lru_cache()
    def COMMITTER_NAME(self):
        committer_name = git(f'log -1 {self.REVISION} --pretty="%cN"')
        return self('COMMITTER_NAME', committer_name)

    @property
    @lru_cache()
    def COMMITTER_EMAIL(self):
        committer_email = git(f'log -1 {self.REVISION} --pretty="%cE"')
        return self('COMMITTER_EMAIL', committer_email)

    @property
    @lru_cache()
    def AUTHORED_BY(self):
        return self('AUTHORED_BY', f'{self.AUTHOR_NAME} <{self.AUTHOR_EMAIL}>')

    @property
    @lru_cache()
    def COMMITTED_BY(self):
        return self('COMMITTED_BY', f'{self.COMMITTER_NAME} <{self.COMMITTER_EMAIL}>')

    @property
    @lru_cache()
    def DEPLOYED_WHEN(self):
        return self("DEPLOYED_WHEN", datetime.utcnow().isoformat())

    @property
    @lru_cache()
    def REVISION(self):
        try:
            return git("rev-parse HEAD")
        except (NotGitRepoError, GitCommandNotFoundError):
            return self("REVISION")

CFG = AutoConfigPlus()
