from hyper import HTTPConnection


class Downloader(object):
    def __init__(self, urls, n):
        conns = [HTTPConnection(url) for url in urls]
