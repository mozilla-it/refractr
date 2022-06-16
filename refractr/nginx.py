import re

from refractr.base import BaseRefract

class NginxRefract(BaseRefract):
    def __init__(self, nginx):
        self.nginx = '\n' + nginx.strip()
        pattern = ' +server_name(( +[^ ;]+)+);'
        match = re.search(pattern, self.nginx)
        srcs = match.group(1).strip().split(' ')
        self.caller = "NginxRefractr"
        super().__init__(srcs=srcs)

    def json(self):
        return dict(
            srcs=self.srcs,
            nginx=self.nginx,
        )

    def render(self):
        return [self.nginx]
