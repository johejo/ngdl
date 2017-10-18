from hyper import HTTP20Connection
from urllib.parse import urlparse, ParseResult
import requests
from hyper.contrib import HTTP20Adapter

from ngdl.utils import get_order

if __name__ == '__main__':
    url = urlparse('http://165.242.111.93:8080/100MB')  # type: ParseResult

    # conn = HTTP20Connection(host=url.hostname, port=url.port)
    # conn.request('GET', url=url.path)
    # resp = conn.get_response()
    # b = resp.read()

    s = requests.Session()
    s.mount('http://165.242.111.93:8080', HTTP20Adapter())
    resp = s.get('http://165.242.111.93:8080/ubuntu-17.04-server-amd64.iso')
    b = resp.content

    with open('100MB', 'wb') as f:
        f.write(b)
