# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import contextlib
import json
import os
import re
from datetime import datetime
from functools import lru_cache
from subprocess import PIPE, CalledProcessError, Popen  # nosec

from decouple import AutoConfig, config

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


@contextlib.contextmanager
def cd(path):
    prev = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


def call(
    cmd, stdout=PIPE, stderr=PIPE, shell=True, nerf=False, throw=True, verbose=False
):

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
            exitcode,
            f"cmd={cmd}; stdout={_stdout}; stderr={_stderr}",
            output=_stdout,
            stderr=_stderr,
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


def branches_contain_ref(ref):
    cmd = f'git branch --contains "{ref}"'
    try:
        _, stdout, _ = call(cmd)
        lines = stdout.strip().split("\n")
        branches = [line[2:] for line in lines if "(" not in line]
        return branches
    except CalledProcessError as cpe:
        return []


class AutoConfigPlus(AutoConfig):  # pylint: disable=too-many-public-methods

    @property
    @lru_cache()
    def REPOROOT(self):
        with cd(os.path.dirname(__file__)):
            reporoot = git("rev-parse --show-toplevel")
        return self("REPOROOT", reporoot)

    @property
    @lru_cache()
    def REPONAME(self):
        reponame = os.path.basename(self.REPOROOT)
        return self("REPONAME", reponame)

    @property
    @lru_cache()
    def AWS_ACCOUNT(self):
        _, stdout, _ = call("aws sts get-caller-identity")
        obj = json.loads(stdout)
        return obj["Account"]

    @property
    @lru_cache()
    def AWS_REGION(self):
        return self("AWS_REGION", "us-west-2")

    @property
    @lru_cache()
    def ECR_REGISTRY(self):
        return self("ECR_REGISTRY", "")

    @property
    @lru_cache()
    def ECR_REPOURL(self):
        if self.ECR_REGISTRY:
            ecr_repourl = f"{self.ECR_REGISTRY}/{self.REPONAME}"
        else:
            ecr_repourl = f"{self.AWS_ACCOUNT}.dkr.ecr.{self.AWS_REGION}.amazonaws.com/{self.REPONAME}"
        return self("ECR_REPOURL", ecr_repourl)

    @property
    @lru_cache()
    def IMAGE_NAME_AND_TAG(self):
        return self("IMAGE_NAME_AND_TAG", f"{self.ECR_REPOURL}:{self.VERSION}")

    # GITHUB Actions env vars
    # https://docs.github.com/en/actions/learn-github-actions/environment-variables#default-environment-variables
    @property
    @lru_cache()
    def GITHUB_REF(self):
        return self("GITHUB_REF", "")

    @property
    @lru_cache()
    def CI(self):
        return self("CI", False)

    @property
    @lru_cache()
    def TAG(self):
        if self.GITHUB_REF.startswith("refs/tags/"):
            return f'{self.GITHUB_REF.split("/")[-1]}'
        return ""

    @property
    @lru_cache()
    def REFRACTR(self):
        return self("REFRACTR", REL)

    @property
    @lru_cache()
    def REFRACTR_YML(self):
        return self(
            "REFRACTR_YML",
            os.path.relpath(f"{REL}/../{self.DEPLOYED_ENV}-refractr.yml"),
        )

    @property
    @lru_cache()
    def SCHEMA_YML(self):
        return self("SCHEMA_YML", f"{self.REFRACTR}/schema.yml")

    @property
    @lru_cache()
    def INGRESS_YAML_TEMPLATE(self):
        return self("INGRESS_YAML_TEMPLATE", f"{self.REFRACTR}/ingress.yaml.template")

    @property
    @lru_cache()
    def IMAGE(self):
        return self("IMAGE", f"{self.REFRACTR}/image")

    @property
    @lru_cache()
    def NGINX(self):
        return self("NGINX", f"{self.REFRACTR}/nginx")

    @property
    @lru_cache()
    def VERSION(self):
        try:
            return git("describe --abbrev=7 --always --tags")
        except (NotGitRepoError, GitCommandNotFoundError):
            return self("VERSION")

    @property
    @lru_cache()
    def BRANCH(self):
        if self.CI:
            if self.GITHUB_REF.startswith("refs/heads/"):
                return f'{self.GITHUB_REF.split("/")[-1]}'

        try:
            return git("rev-parse --abbrev-ref HEAD")
        except (NotGitRepoError, GitCommandNotFoundError):
            return self("BRANCH")

    @property
    @lru_cache()
    def PUBLISH_BRANCHES(self):
        branches = self("PUBLISH_BRANCHES", None)
        if branches:
            return branches.split(",")
        return ["main"]

    @property
    @lru_cache()
    def PROD_TAG_PATTERN(self):
        return self("PROD_TAG_PATTERN", "^(v[0-9]+\.[0-9]+\.[0-9]+)$")

    @property
    @lru_cache()
    def DEPLOYED_ENV(self):
        if self.CI:
            match = re.search(self.PROD_TAG_PATTERN, self.VERSION)
            if match:
                return "prod"
            else:
                return "stage"
        return "dev"

    @property
    @lru_cache()
    def AUTHOR_NAME(self):
        author_name = git(f'log -1 {self.REVISION} --pretty="%aN"')
        return self("AUTHOR_NAME", author_name)

    @property
    @lru_cache()
    def AUTHOR_EMAIL(self):
        author_email = git(f'log -1 {self.REVISION} --pretty="%aE"')
        return self("AUTHOR_EMAIL", author_email)

    @property
    @lru_cache()
    def COMMITTER_NAME(self):
        committer_name = git(f'log -1 {self.REVISION} --pretty="%cN"')
        return self("COMMITTER_NAME", committer_name)

    @property
    @lru_cache()
    def COMMITTER_EMAIL(self):
        committer_email = git(f'log -1 {self.REVISION} --pretty="%cE"')
        return self("COMMITTER_EMAIL", committer_email)

    @property
    @lru_cache()
    def AUTHORED_BY(self):
        return self("AUTHORED_BY", f"{self.AUTHOR_NAME} <{self.AUTHOR_EMAIL}>")

    @property
    @lru_cache()
    def COMMITTED_BY(self):
        return self("COMMITTED_BY", f"{self.COMMITTER_NAME} <{self.COMMITTER_EMAIL}>")

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
