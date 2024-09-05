from nginx.config.api import KeyMultiValueOption, KeyValueOption, Location, Section

from refractr.base import BaseRefract, create_target
from refractr.url import URL


class SimpleRefract(BaseRefract):
    def __init__(
        self, dsts, srcs, status, headers, hsts_img, preserve_path, wildcard_file
    ):
        super().__init__(
            dsts, srcs, status, headers, hsts_img, preserve_path, wildcard_file
        )

    @property
    def dst(self):
        assert self.dsts and len(self.dsts) == 1, f"self.dsts={self.dsts}"
        return self.dsts[0]

    def generate_tests(self):
        tests = [{URL(src).http: URL(self.dst).https} for src in self.srcs]
        if self.preserve_path and URL(self.dst).path == "/":
            tests += [
                {URL(src, path="path").http: URL(self.dst, path="path").https}
                for src in self.srcs
            ]
        return tests

    def render(self):
        server_name = KeyValueOption("server_name", self.server_name)
        redirect = KeyMultiValueOption(
            "return",
            [
                self.status,
                create_target(self.dst, self.preserve_path),
            ],
        )
        stmts = []
        if self.headers:
            stmts += [
                self.render_headers(),
            ]
        if self.hsts_img:
            stmts += [
                self.render_hsts_img(),
            ]
        stmts += [redirect]
        return [
            Section(
                "server",
                server_name,
                *stmts,
            )
        ]
