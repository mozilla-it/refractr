from leatherman.dictionary import head_body
from leatherman.repr import __repr__
from nginx.config.api import KeyValueOption, Location
from nginx.config.helpers import duplicate_options
from yaml import dump

from refractr.cfg import CFG, cd
from refractr.url import URL
from refractr.utils import *

WILDCARD = "wildcard"
REQUEST_URI = "$request_uri"


def preserve(url):
    if url.endswith("/"):
        return url[0:-1] + REQUEST_URI
    return url + REQUEST_URI


def create_target(dst, preserve_path=True):
    url = URL(dst).https
    # urllib may return "a slightly different, but equivalent URL"
    # which may remove a trailing '?' - the trailing '?' is used in the
    # nginx confguration to indicate that query params should not be appended.
    # The trailing '?' is only present in nginx.conf, not the redireceted url
    # (https://github.com/python/cpython/blob/main/Lib/urllib/parse.py#L483-L492)
    if not url.endswith("?") and dst.endswith("?"):
        url += "?"
    if preserve_path and URL(dst).path == "/":
        return preserve(url)
    return url


def tuplify(obj):
    if isinstance(obj, dict):
        return obj
    elif isinstance(obj, (list, tuple)):
        return tuple(obj)
    elif obj != None:
        return (obj,)
    return obj


def listify(obj):
    if isinstance(obj, tuple):
        return list(obj)
    return obj


def lowercase(items):
    return [item.lower() for item in items]


class BaseRefract:
    def __init__(
        self,
        dsts=None,
        srcs=None,
        status=None,
        headers=None,
        hsts_img=False,
        preserve_path=False,
        wildcard_file=None,
        tests=None,
    ):
        self.dsts = tuplify(dsts)
        self._srcs = tuplify(srcs)
        self.status = status
        self.headers = headers
        self.hsts_img = hsts_img
        self.preserve_path = preserve_path
        self.wildcard_file = wildcard_file

        extra_tests = []
        if hasattr(self, "generate_tests"):
            extra_tests = self.generate_tests()

        self.tests = tuplify((tests or []) + extra_tests)

    def __str__(self):
        return dump(self.json(), explicit_start=True, default_flow_style=False)

    __repr__ = __repr__

    @property
    def src(self):
        if self.srcs:
            assert isinstance(self.srcs, tuple) and len(self.srcs) > 0, type(self.srcs)
            return self.srcs[0]
        return None

    @property
    def srcs(self):
        if self.wildcard_file:
            srcs = []
            for src in self._srcs:
                if src.startswith(WILDCARD):
                    for subdomain in self.wildcard_extrapolated_subdomains:
                        src1 = subdomain + src[len(WILDCARD) :]
                        srcs.append(src1)
                else:
                    srcs.append(src)
            return tuplify(lowercase(srcs))
        return tuplify(lowercase(self._srcs))

    @property
    def balance(self):
        """
        generated tests will always match location redirects
        rewrites do no generate tests; so this is to help identify that
        """
        if hasattr(self, "caller") and self.caller == "NginxRefractr":
            return 0
        dst_count = len(self.dsts) if isinstance(self.dsts, list) else 1
        test_count = len(self.tests)
        return test_count - dst_count

    @property
    def wildcard_extrapolated_subdomains(self):
        with cd(CFG.REPOROOT):
            return [
                line
                for line in open(self.wildcard_file).read().strip().split("\n")
                if not line.startswith("#")
            ]

    def json(self):
        return dict(
            dsts=listify(self.dsts),
            srcs=listify(self.srcs),
            status=self.status,
            headers=self.headers,
            hsts_img=self.hsts_img,
            preserve_path=self.preserve_path,
            wildcard_file=self.wildcard_file,
            tests=listify(self.tests),
        )

    def render_headers(self):
        return duplicate_options(
            "add_header",
            [list(item) for item in self.headers.items()],
        )

    def render_hsts_img(self):
        return Location("/set_hsts.gif", KeyValueOption("return", 200))

    @property
    def server_name(self):
        if self.wildcard_file:
            nltab = "\n" + " " * 8
            return join([nltab + URL(src).netloc for src in self.srcs])
        return join([URL(src).netloc for src in self.srcs])

    @property
    def server_name_include(self):
        return self.srcs[0] + ".include"

    def render(self):
        raise NotImplementedError
