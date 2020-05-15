from nginx.config.api import KeyValueOption
from nginx.config.api import KeyMultiValueOption
from nginx.config.api import Section
from leatherman.dictionary import head_body

from refractr.base import BaseRefract
from refractr.url import URL

def status_to_word(status):
    return {
        301: 'permanent',
        302: 'redirect', # this is what is used for 'temporary'
    }[status]

class RewriteRefract(BaseRefract):
    def __init__(self, dst, srcs, status, tests):
        assert dst
        assert isinstance(dst, list)
        super().__init__(dst, srcs, status, tests)

    def render_refract(self):
        server_name = KeyValueOption('server_name', self.server_name)
        rewrites = []
        for dst in self.dst:
            if_ = dst.pop('if', None)
            redirect = dst.pop('redirect', None)
            try:
                match, target = head_body(dst)
                rewrite = KeyMultiValueOption(
                    'rewrite', [
                        match,
                        URL(target).https,
                        status_to_word(self.status),
                    ],
                )
                if if_:
                    rewrite = Section(f'if ({if_})', rewrite)
                rewrites += [rewrite]
            except:
                if redirect == None:
                    raise
            if redirect:
                rewrites += [KeyMultiValueOption(
                    'return', [
                        self.status,
                        URL(redirect).https,
                    ],
                )]
        return Section(
            'server',
            server_name,
            *rewrites,
        )
