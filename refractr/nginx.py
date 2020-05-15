from refractr.base import BaseRefract

class NginxRefract(BaseRefract):
    def __init__(self, nginx, tests):
        self.nginx = nginx
        super().__init__(tests=tests)

    def render_refract(self):
        return self.nginx
