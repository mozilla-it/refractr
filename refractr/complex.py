import re

from nginx.config.api import KeyValueOption
from nginx.config.api import KeyMultiValueOption
from nginx.config.api import Section, Location
from leatherman.dictionary import head, head_body

from refractr.exceptions import NonIfDstFoundError
from refractr.base import BaseRefract
from refractr.url import URL

def match_to_path(match):
    pattern = r'^\^(.+)\(.+\)'
    m = re.search(pattern, match)
    if m:
        path = m.group(1)
    else:
        raise LocationNotFoundInRewriteMatchError(match)
    return path

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

    def render_redirect(self, path, target, status=None, location=False):
        redirect = KeyMultiValueOption(
            'return', [
                status or self.status,
                URL(target),
            ]
        )
        if location:
            return Location(
                f'= {path}',
                redirect,
            )
        return redirect

    def render_rewrite(self, match, target, status=None, location=False):
        rewrite = KeyMultiValueOption(
            'rewrite', [
                match,
                URL(target).https,
                status_to_word(status or self.status),
            ]
        )
        if location:
            path = match_to_path(match)
            return Location(
                path,
                rewrite,
            )
        return rewrite

    def render_if(self, dst, status):
        sections = []
        if_ = dst.pop('if', None)
        redirect = dst.pop('redirect', None)
        try:
            match, target = head_body(dst)
            rewrite = self.render_rewrite(match, target, status)
            if if_:
                rewrite = Section(f'if ({if_})', rewrite)
            sections += [rewrite]
        except:
            if redirect == None:
                raise
        if redirect:
            sections += [self.render_redirect(None, target, status)]
        return sections

    def render(self):
        server_name = KeyValueOption('server_name', self.server_name)
        sections = []
        for dst in self.dst:
            if isinstance(dst, str):
                sections += [self.render_redirect(None, dst)]
            status = dst.pop('status', self.status)
            if 'if' in dst:
                sections += self.render_if(dst, status)
                continue
            try:
                key, value = head_body(dst)
            except:
                raise NonIfDstFoundError(dst, status)
            if key.startswith('/'):
                sections += [self.render_redirect(key, value, status, location=True)]
            elif key.startswith('^/'):
                sections += [self.render_rewrite(key, value, status, location=True)]
            elif key == 'redirect':
                sections += [self.render_redirect(None, value, status)]

        return [Section(
            'server',
            server_name,
            *sections,
        )]
