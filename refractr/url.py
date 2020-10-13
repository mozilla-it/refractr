from urllib.parse import urlparse, ParseResult
from collections import UserString
from refractr.exceptions import URLError
from refractr.utils import *

REQUEST_URI = '$request_uri'

# makes visualizing as string easier to read
ParseResult.__repr__ = lambda self: self.geturl()

def replace(pr, **kwargs):
    if kwargs:
        return ParseResult(
            scheme=kwargs.get('scheme', pr.scheme),
            netloc=kwargs.get('netloc', pr.netloc),
            path=kwargs.get('path', pr.path),
            params=kwargs.get('params', pr.params),
            query=kwargs.get('query', pr.query),
            fragment=kwargs.get('fragment', pr.fragment))
    return pr

def preserve(url):
    if url.endswith('/'):
        return url[0:-1] + REQUEST_URI
    return url + REQUEST_URI

class URL(UserString):
    def __init__(self, url, preserve_path=False, **kwargs):
        if url:
            if url.startswith('http'):
                self._pr = urlparse(url)
            else:
                self._pr = urlparse(f'https://{url}')
            self._pr = replace(self._pr, **kwargs)
        else:
            raise URLError(url)
        self.preserve_path = preserve_path

    @property
    def http(self):
        url = replace(self._pr, scheme='http').geturl()
        if self.preserve_path:
            return preserve(url)
        return url

    @property
    def https(self):
        url = replace(self._pr, scheme='https').geturl()
        if self.preserve_path:
            return preserve(url)
        return url

    @property
    def url(self):
        return self._pr.geturl()

    # required property for UserString
    @property
    def data(self):
        return self._pr.geturl()

    @property
    def scheme(self):
        return self._pr.scheme

    @scheme.setter
    def scheme(self, scheme):
        self._pr = replace(self._pr, scheme=scheme)

    @property
    def netloc(self):
        return self._pr.netloc

    @netloc.setter
    def netloc(self, netloc):
        self._pr = replace(self._pr, netloc=netloc)

    @property
    def path(self):
        return self._pr.path

    @path.setter
    def path(self, path):
        self._pr = replace(self._pr, path=path)

    @property
    def params(self):
        return self._pr.params

    @params.setter
    def params(self, params):
        self._pr = replace(self._pr, params=params)

    @property
    def query(self):
        return self._pr.query

    @query.setter
    def query(self, query):
        self._pr = replace(self._pr, query=query)

    @property
    def fragment(self):
        return self._pr.frament

    @fragment.setter
    def fragment(self, fragment):
        self._pr = replace(self._pr, fragment=fragment)
