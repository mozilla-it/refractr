from nginx.config.api import KeyValueOption
from nginx.config.api import KeyMultiValueOption
from nginx.config.api import Section, Location
from leatherman.dictionary import head, head_body

from refractr.base import BaseRefract
from refractr.url import URL

def status_to_word(status):
    return {
        301: 'permanent',
        302: 'redirect', # this is what is used for 'temporary'
    }[status]

def create_test(src, path, target):
    if path.endswith('*'):
        given = URL(f'{src}{path[:-1]}splat').http
        if '$splat' in target:
            target = target.replace('$splat', 'splat')
        else:
            target = f'{target}splat'
        expect = URL(target).https
    else:
        given = URL(f'{src}{path}').http
        expect = URL(target).https
    return {
        given: expect
    }

class ComplexRefract(BaseRefract):
    def __init__(self, dst, srcs, status, tests=None):
        assert dst and isinstance(dst, list)
        tests = tests or []
        for src in srcs:
            for item in dst:
                try:
                    path, target = head_body(item)
                    if path.startswith('/'):
                        tests += [create_test(src, path, target)]
                except:
                    continue
        super().__init__(dst, srcs, status, tests)

    def render_splat(self, path, target, status):
        path = path[:-1]
        if '$splat' not in target:
            target = f'{target}$splat'
        return [Location(
            # without '=', prefix match
            path,
            KeyMultiValueOption(
                'rewrite', [
                    f'{path}(?<splat>.*)',
                    URL(target).https,
                    status_to_word(status),
                ],)
        )]

    def render_location(self, dst, status):
        path, target = head_body(dst)
        if path.endswith('*'):
            return self.render_splat(path, target, status)
        return [Location(
            # '=' is exact match
            f'= {path}',
            KeyMultiValueOption(
                'return', [
                    status,
                    URL(target).https
                ]),
        )]

    def render_rewrite(self, dst, status):
        rewrites = []
        if_ = dst.pop('if', None)
        redirect = dst.pop('redirect', None)
        try:
            match, target = head_body(dst)
            rewrite = KeyMultiValueOption(
                'rewrite', [
                    match,
                    URL(target).https,
                    status_to_word(status),
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
                    status,
                    URL(redirect).https,
                ]
            )]
        return rewrites

    def render(self):
        server_name = KeyValueOption('server_name', self.server_name)
        blocks = []
        for dst in self.dst:
            status = dst.pop('status', self.status)
            try:
                key = head(dst)
            except:
                key = None
            if key and key.startswith('/'):
                blocks += self.render_location(dst, status)
            else:
                blocks += self.render_rewrite(dst, status)

        return [Section(
            'server',
            server_name,
            *blocks,
        )]
