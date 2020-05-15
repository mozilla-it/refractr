from refractr.base import BaseRefract
from refractr.utils import *
from refractr.url import URL

class SimpleRefract(BaseRefract):
    def __init__(self, dst, srcs, status):
        tests = [
            {URL(src).http: URL(dst).https}
            for src
            in srcs
        ]
        super().__init__(dst, srcs, status, tests)

    def render_refract(self):
        server_name = kvo('server_name', self.server_name)
        return Section(
            'server',
            server_name,
            kmvo('return', self.status, URL(self.dst).https)
        )
