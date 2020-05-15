from nginx.config.api import KeyValueOption
from nginx.config.api import KeyMultiValueOption
from nginx.config.api import Section, Location
from leatherman.dictionary import head_body

from refractr.base import BaseRefract
from refractr.url import URL

class RedirectRefract(BaseRefract):
    def __init__(self, dst, srcs, status, tests=None):
        if tests == None:
            tests = []
            for src in srcs:
                for item in dst:
                    path, target = head_body(item)
                    given = URL(f'{src}{path}').http
                    expect = URL(target).https
                    tests += [{
                        given: expect
                    }]
        super().__init__(dst, srcs, status, tests)

    def render_refract(self):
        server_name = KeyValueOption('server_name', self.server_name)
        locations = []
        for dst in self.dst:
            path, target = head_body(dst)
            locations += [Location(
                path,
                KeyMultiValueOption(
                    'return', [
                        self.status,
                        URL(target).https
                    ]),
            )]
        return Section(
            'server',
            server_name,
            *locations,
        )
