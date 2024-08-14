#!/usr/bin/env python3

import json
import os
import re
from functools import lru_cache

from doit.tools import LongRunning
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from ruamel.yaml import safe_load

from refractr.cfg import CFG, CalledProcessError, call, git

IMAGE = "itsre/refractr"

DOIT_CONFIG = {
    "default_tasks": ["test"],
    "verbosity": 2,
}


@lru_cache()
def envs(sep=" ", **kwargs):
    envs = dict(
        REFRACTR_VERSION=CFG.VERSION,
        PAPERTRAIL_URL=CFG.PAPERTRAIL_URL,
    )
    return sep.join(
        [f"{key}={value}" for key, value in sorted(dict(envs, **kwargs).items())]
    )


def write_json(filename, **items):
    with open(filename, "w") as f:
        f.write(json.dumps(items, indent=4, sort_keys=True))


def task_deployed():
    """
    write refractr/deployed json file
    """
    items = dict(
        DEPLOYED_BY=CFG.COMMITTED_BY,
        DEPLOYED_ENV=CFG.DEPLOYED_ENV,
        DEPLOYED_WHEN=CFG.DEPLOYED_WHEN,
    )
    if CFG.COMMITTED_BY != CFG.AUTHORED_BY:
        items.update(AUTHORED_BY=CFG.AUTHORED_BY)
    return {
        "actions": [lambda: write_json(f"{CFG.IMAGE}/deployed", **items)],
    }


def task_version():
    """
    write refractr/version json file
    """
    items = dict(
        BRANCH=CFG.BRANCH,
        REVISION=CFG.REVISION,
        VERSION=CFG.VERSION,
    )
    return {
        "actions": [lambda: write_json(f"{CFG.IMAGE}/version", **items)],
    }


def task_schema():
    """
    test refractr.yml against schema.yml using jsonschema
    """

    def schema():
        assert os.path.isfile(CFG.REFRACTR_YML)
        assert os.path.isfile(CFG.SCHEMA_YML)
        print(f"validating {CFG.REFRACTR_YML} against {CFG.SCHEMA_YML} =>", end=" ")
        with open(CFG.REFRACTR_YML, "r") as f:
            refractr_yml = safe_load(f)
        with open(CFG.SCHEMA_YML, "r") as f:
            schema_yml = safe_load(f)
        try:
            validate(refractr_yml, schema_yml)
            print("SUCCESS")
            return True
        except ValidationError as ve:
            print("FAILURE")
            print(ve)
            return False

    return {
        "task_dep": [],
        "actions": [
            schema,
        ],
    }


def task_nginx():
    """
    generate nginx.conf files from refractr.yml
    """
    cmd = f"bin/refractr nginx > {CFG.NGINX}/conf.d/refractr.conf"
    return {
        "task_dep": [
            "schema",
        ],
        "actions": [
            cmd,
            f'echo "{cmd}"',
        ],
    }


def task_ingress():
    """
    create ingress.yaml from refractr.yml domains and ingress.yaml.template
    """
    ingress_yaml = os.path.basename(CFG.INGRESS_YAML_TEMPLATE.replace(".template", ""))
    cmd = f"bin/refractr ingress --ingress-template {CFG.INGRESS_YAML_TEMPLATE} > {CFG.IMAGE}/{ingress_yaml}"
    return {
        "task_dep": [
            "schema",
        ],
        "actions": [
            cmd,
            f'echo "{cmd}"',
        ],
    }


def task_refracts():
    """
    create refracts.json from loading refractr.yml
    """
    cmd = f"bin/refractr --output json show > {CFG.IMAGE}/refracts"
    return {
        "task_dep": [
            "schema",
        ],
        "actions": [
            cmd,
            f'echo "{cmd}"',
        ],
    }


def task_build():
    """
    run docker compose build for refractr
    """
    return {
        "task_dep": [
            "deployed",
            "version",
            "nginx",
            "ingress",
            "refracts",
        ],
        "actions": [
            f"env {envs()} docker compose build refractr",
        ],
    }


def task_check():
    """
    run nginx -t test on refractr nginx config
    """
    return {
        "task_dep": [
            "build",
        ],
        "actions": [
            f"env {envs()} docker compose run refractr check",
        ],
    }


def task_drun():
    """
    run refractr container via docker compose up -d
    """
    return {
        "task_dep": [
            "check",
        ],
        "actions": [
            # https://github.com/docker/compose/issues/1113#issuecomment-185466449
            f"env {envs()} docker compose rm --force refractr",
            LongRunning(
                f"nohup env {envs()} docker compose up -d --remove-orphans refractr >/dev/null &"
            ),
        ],
    }


def task_test():
    """
    run pytest tests against the locally running container
    """
    return {
        "task_dep": [
            "build",
            "drun",
        ],
        "actions": [
            "sleep 1",
            "PYTHONPATH=. python3 -m pytest -vv -q -s",
        ],
    }


def task_show():
    """
    show CI variables
    """

    def show():
        print(
            f"CI={CFG.CI} "
            f"TAG={CFG.TAG} "
            f"VERSION={CFG.VERSION} "
            f"BRANCH={CFG.BRANCH} "
            f"DEPLOYED_ENV={CFG.DEPLOYED_ENV}"
        )

    return {
        "actions": [
            show,
        ]
    }


def task_publish():
    """
    publish docker image to aws ECR
    """

    def publish():
        call(f"docker tag refractr:{CFG.VERSION} {CFG.IMAGE_NAME_AND_TAG}")
        call(f"docker push {CFG.IMAGE_NAME_AND_TAG}")
        print(f"publishing {CFG.VERSION}")

    return {
        "task_dep": [
            "test",
        ],
        "actions": [
            publish,
        ],
    }


def task_refractslisting():
    """
    create refracts list  from loading refractr.json
    """
    cmd = f"bin/refractr --output json show > {CFG.IMAGE}/refracts.json"
    cmd1 = "bin/refracts-listing"
    return {
        "task_dep": [
            "schema",
        ],
        "actions": [
            cmd,
            cmd1,
            f'echo "{cmd1}"',
        ],
    }


def task_certificate_manager_input():
    """
    create input file for certificate manager tf module
    """

    cmd = f"bin/refractr --output yaml cmi > {CFG.IMAGE}/certificate_manager_input.yaml"

    return {
        "task_dep": ["schema"],
        "actions": [cmd, f'echo "{cmd}"'],
    }
