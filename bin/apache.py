#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import errno
import os
import re
import sys
from pathlib import Path

import click
from leatherman.fuzzy import fuzzy
from leatherman.output import default_output, output_print


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as ex:  # Python >2.5
        if ex.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_redirects(content):
    pattern = "((#.*\n)*(<VirtualHost [^>]+>+\n(\n| +.*\n)+</VirtualHost>\n){1,2})"
    regex = re.compile(pattern)
    matches = regex.findall(content)
    return [match[0] for match in matches if "ServerName" in match[2]]


def get_servername_and_redirect(content):
    pattern = "ServerName ([^ \n]+)"
    regex = re.compile(pattern)
    match = regex.search(content)
    servername = match.group(1)
    https = "https://"
    if servername.startswith(https):
        servername = servername[len(https) :]
    return servername, content


def create_redirect_file(filename, content):
    mkdir_p("redirects")
    with open(f"redirects/{filename}", "w") as f:
        f.write(content)


def divine_filepath(dirpath, filename):
    if os.path.exists(filename):
        return filename
    try:
        return Path(dirpath).glob(f"**/{filename}").__next__()
    except Exception as ex:
        raise Exception(f"error {filename} not found!") from ex


@click.command()
@click.option(
    "-c", "--create-files", is_flag=True, help="toggle creating redirect files"
)
@click.option(
    "-o", "--output", default=default_output(), help="toggle json or yaml output"
)
@click.option("-s", "--servername-only", is_flag=True, help="only print the servername")
@click.option(
    "-f",
    "--filename",
    default="redirects.mozilla.org.conf",
    help='give path to file, or it will "find" it',
)
@click.option(
    "-p",
    "--dirpath",
    default=os.path.expanduser("~"),
    help="change starting path for searching for filename",
)
@click.argument("patterns", nargs=-1)
def cli(
    create_files=None,
    output=None,
    servername_only=None,
    filename=None,
    dirpath=None,
    patterns=None,
):
    if patterns == None:
        patterns = ("*",)
    filepath = divine_filepath(dirpath, filename)
    content = open(filepath).read()
    redirects = dict(
        [get_servername_and_redirect(redirect) for redirect in get_redirects(content)]
    )
    redirects = fuzzy(redirects).include(*patterns).defuzz()
    if create_files:
        [
            create_redirect_file(filename, content)
            for filename, content in redirects.items()
        ]
    if servername_only:
        output_print(dict(redirects=list(redirects.keys())), output)
    else:
        output_print(dict(redirects=redirects), output)


if __name__ == "__main__":
    cli()
