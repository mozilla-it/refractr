class URLError(Exception):
    def __init__(self, url):
        msg = f'error with url={url}'
        super().__init__(msg)
