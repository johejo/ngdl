from hyper import HTTPConnection
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, ParseResult
from typing import List
import queue

from logging import getLogger, NullHandler, StreamHandler, DEBUG

from .exceptions import PortError, StatusCodeError, NoContentLength, FileSizeError, URIError, NotAcceptRangeHeader
from .utils import map_all

local_logger = getLogger(__name__).addHandler(NullHandler)


class Downloader(object):
    def __init__(self, urls, parallel_num=1, split_size=1, *, logger=None):
        """

        :param list urls:
        :param int parallel_num:
        :param int split_size:
        :param logger:
        """

        logger = logger or local_logger
        self._parallel_num = parallel_num
        self._split_size = split_size

        self._urls = []  # type: List[ParseResult]
        self._conns = []  # type: List[HTTPConnection]
        self._ports = []
        self._length_list = []

        for url in urls:
            self._conns.append(self._check_url(url, logger=logger))
            self._urls.append(urlparse(url))

        if map_all(self._length_list) is False:
            raise FileSizeError

        self._request_queue = queue.Queue()
        logger.debug(msg='Successfully initialized')

    def _check_url(self, url, *, logger=None):
        """

        :param url: str
        :return: conn
        """
        logger = logger or local_logger
        parsed_url = urlparse(url)  # type: ParseResult

        if parsed_url.netloc == '':
            raise URIError

        if parsed_url.scheme == '' or parsed_url.scheme == 'http':
            if parsed_url.port is None:
                port = 80
            else:
                port = parsed_url.port

        elif parsed_url.scheme == 'https':
            if parsed_url.port is None:
                port = 443
            else:
                port = parsed_url.port

        else:
            raise PortError

        return self._check_status(url, port, logger=logger)  # type: HTTPConnection

    def _check_status(self, url, port, *, logger=None):
        """

        :param url: str
        :param port: int
        :param logger: logger
        :return: conn
        """
        logger = logger or local_logger

        parsed_url = urlparse(url)  # type: ParseResult
        conn = HTTPConnection(host=parsed_url.hostname, port=port, enable_push=True)
        stream_id = conn.request(method='HEAD', url=parsed_url.path)
        resp = conn.get_response()
        status = resp.status
        if 301 <= status <= 303 or 307 <= status <= 308:
            location = resp.headers['Location']
            logger.debug(msg='Host is redirected to {0}'.format(location))
            conn = self._check_url(url=location)

        elif status != 200:
            logger.debug(msg='Invalid status code: {0}'.format(str(status)))
            raise StatusCodeError

        try:
            # print(resp.headers['Content-Length'][0])
            length = (resp.headers['Content-Length'][0])
        except KeyError:
            raise NoContentLength

        try:
            resp.headers[b'Accept-Ranges']
        except KeyError:
            raise NotAcceptRangeHeader

        self._length_list.append(length)

        return conn  # type: HTTPConnection

    def download(self):
        pass

    def _is_finished(self):
        return False
