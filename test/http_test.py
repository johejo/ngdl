from hyper import HTTP20Connection as hc
from urllib.parse import urlparse, ParseResult

from ngdl.utils import get_order

if __name__ == '__main__':
    url = urlparse('http://165.242.111.93:8080/100MB')  # type: ParseResult

    conn = hc(host=url.hostname, port=url.port)
    conn.request('GET', url=url.path)
    resp = conn.get_response()
    with open('100MB', 'wb') as f:
        f.write(resp.read())
    print(resp.status)
