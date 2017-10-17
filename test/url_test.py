from ngdl import Downloader
from ngdl.exceptions import *
import sys

from logging import getLogger, StreamHandler, DEBUG

handler = StreamHandler()
handler.setLevel(DEBUG)
local_logger = getLogger(__name__)
local_logger.setLevel(DEBUG)
local_logger.addHandler(handler)

if __name__ == '__main__':

    try:
        assert Downloader(urls=['foo'], logger=local_logger)
    except URIError:
        print('SUCCESS 0', file=sys.stderr)

    try:
        assert Downloader(urls=['foo.bar'], logger=local_logger)
    except URIError:
        print('SUCCESS 1', file=sys.stderr)

    try:
        assert Downloader(urls=['foo.bar/buzz'], logger=local_logger)
    except URIError:
        print('SUCCESS 2', file=sys.stderr)

    try:
        assert Downloader(urls=['ftp://foo.bar/buzz'], logger=local_logger)
    except PortError:
        print('SUCCESS 3', file=sys.stderr)

    # assert Downloader(urls=['http://165.242.111.77/100MB'], logger=local_logger)
    assert Downloader(urls=['http://165.242.111.93:8080/100MB'], logger=local_logger)
    assert Downloader(urls=['https://165.242.111.93:8081/100MB'], logger=local_logger)

    # try:
    #     assert Downloader(urls=['https://www.hiroshima-cu.ac.jp/'], logger=local_logger)
    # except NoContentLength:
    #     print('SUCCESS 4', file=sys.stderr)

    assert Downloader(urls=['http://www.ftp.ne.jp/Linux/packages/ubuntu/releases-cd/17.04/ubuntu-17.04-server-amd64.iso'], logger=local_logger)

    urls0 = [
        'http://165.242.111.77/100MB',
        'http://165.242.111.93:8080/100MB',
        'https://165.242.111.93:8080/100MB'
    ]

    assert Downloader(urls=urls0, logger=local_logger)

    urls1 = [
        'http://www.ftp.ne.jp/Linux/packages/ubuntu/releases-cd/17.04/ubuntu-17.04-server-amd64.iso',   # KDDI
        'http://ubuntutym2.u-toyama.ac.jp/ubuntu/17.04/ubuntu-17.04-server-amd64.iso',                  # toyama
        'http://ftp.riken.go.jp/Linux/ubuntu-releases/17.04/ubuntu-17.04-server-amd64.iso',             # riken
        'http://ftp.jaist.ac.jp/pub/Linux/ubuntu-releases/17.04/ubuntu-17.04-server-amd64.iso',         # jaist
        'http://ftp.yz.yamagata-u.ac.jp/pub/linux/ubuntu/releases/17.04/ubuntu-17.04-server-amd64.iso'  # yamagata
    ]

    assert Downloader(urls=urls1, logger=local_logger)
    print('SUCCESS 4', file=sys.stderr)

    urls2 = urls0 + urls1
    try:
        assert Downloader(urls=urls2, logger=local_logger)
    except FileSizeError:
        print('SUCCESS 5', file=sys.stderr)
