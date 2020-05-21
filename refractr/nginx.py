import re

from refractr.base import BaseRefract

class NginxRefract(BaseRefract):
    def __init__(self, nginx, tests):
        self.nginx = '\n' + nginx.strip()
        pattern = ' +server_name(( +[^ ;]+)+);'
        match = re.search(pattern, self.nginx)
        srcs = match.group(1).strip().split(' ')
        super().__init__(srcs=srcs, tests=tests)

    def json(self):
        return dict(
            srcs=self.srcs,
            nginx=self.nginx,
            tests=self.tests,
        )

    def render(self):
        return [self.nginx]
