from nginx.config.api import KeyValueOption
from nginx.config.api import KeyMultiValueOption
from nginx.config.api import Section

from refractr.base import BaseRefract
from refractr.url import URL

class SimpleRefract(BaseRefract):
    def __init__(self, dsts, srcs, status):
        tests = [
            {URL(src).http: URL(dsts).https}
            for src
            in srcs
        ]
        super().__init__(dsts, srcs, status, tests)

    def render(self):
        server_name = KeyValueOption('server_name', self.server_name)
        return [Section(
            'server',
            server_name,
            KeyMultiValueOption(
                'return', [
                    self.status,
                    URL(self.dsts).https
                ]
            )
        )]
