from nginx.config.api import KeyValueOption
from nginx.config.api import KeyMultiValueOption
from nginx.config.api import Section

from refractr.base import BaseRefract
from refractr.url import URL

class SimpleRefract(BaseRefract):
    def __init__(self, dsts, srcs, status, preserve_path):
        super().__init__(dsts, srcs, status, preserve_path)

    @property
    def dst(self):
        assert self.dsts and len(self.dsts) == 1, f'self.dsts={self.dsts}'
        return self.dsts[0]

    def generate_tests(self):
        tests = [
            {URL(src).http: URL(self.dst).https}
            for src
            in self.srcs
        ]
        if self.preserve_path:
            tests += [
                {URL(src, path='path').http: URL(self.dst, path='path').https}
                for src
                in self.srcs
            ]
        return tests

    def render(self):
        server_name = KeyValueOption('server_name', self.server_name)
        target = URL(self.dst)
        return [Section(
            'server',
            server_name,
            KeyMultiValueOption(
                'return', [
                    self.status,
                    URL(self.dst, self.preserve_path).https,
                ]
            )
        )]
