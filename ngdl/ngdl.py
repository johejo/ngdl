from hyper import HTTP20Connection
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError
from urllib.parse import urlparse, ParseResult
from typing import List
from collections import deque
from random import randrange

from logging import getLogger, NullHandler

from .exceptions import PortError, StatusCodeError, NoContentLength, FileSizeError, URIError, NoAcceptRangeHeader
from .utils import map_all, get_order

local_logger = getLogger(__name__).addHandler(NullHandler)


class Downloader(object):
    def __init__(self, urls, parallel_num=1, split_size=1, *, logger=None):
        """

        :param list urls:
        :param int parallel_num:
        :param int split_size:
        :param logger:
        """

        self.logger = logger or local_logger
        self._parallel_num = parallel_num
        self._split_size = split_size

        self._urls = []  # type: List[ParseResult]
        self._conns = []  # type: List[HTTP20Connection]
        self._ports = []
        self._length_list = []

        for url in urls:
            self._conns.append(self._check_url(url))
            self._urls.append(urlparse(url))

        if map_all(self._length_list) is False:
            raise FileSizeError
        length = int(self._length_list[0])

        begin = 0
        self._request_num = length // split_size
        reminder = length % split_size
        if reminder != 0:
            self._request_num += 1

        self._request_queue = deque()

        for i in range(self._request_num):

            if reminder != 0 and i == self._request_num - 1:
                end = begin + reminder - 1
            else:
                end = begin + split_size - 1

            param = {'index': i,
                     'method': 'GET',
                     'url': self._urls[0].path,
                     'headers': {'Range': 'bytes={0}-{1}'.format(begin, end)}
                     }
            self._request_queue.append(param)
            begin += split_size

        # self._result_queue = deque()

        self.WORKER_NUM = 5
        self.GET_TIMEOUT = 1
        self._received_index = 0
        self._future_resp = []  # type: List[Future]
        self._data = [None for i in range(self._request_num)]
        self._executor = ThreadPoolExecutor()

        self.logger.debug(msg='Successfully initialized')

    def _check_url(self, url):
        """

        :param url: str
        :return: conn
        """
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

        return self._check_status(url, port)  # type: HTTP20Connection

    def _check_status(self, url, port):
        """

        :param url: str
        :param port: int
        :return: conn
        """

        parsed_url = urlparse(url)  # type: ParseResult
        conn = HTTP20Connection(host=parsed_url.hostname, port=port, enable_push=True)
        conn.request(method='HEAD', url=parsed_url.path)
        resp = conn.get_response()
        status = resp.status
        if 301 <= status <= 303 or 307 <= status <= 308:
            location = resp.headers['Location']
            self.logger.debug(msg='Host is redirected to {0}'.format(location))
            conn = self._check_url(url=location)

        elif status != 200:
            self.logger.debug(msg='Invalid status code: {0}'.format(str(status)))
            raise StatusCodeError

        try:
            length = (resp.headers['Content-Length'][0])
        except KeyError:
            raise NoContentLength

        try:
            resp.headers[b'Accept-Ranges']
        except KeyError:
            raise NoAcceptRangeHeader

        self._length_list.append(length)

        return conn  # type: HTTP20Connection

    def start_download(self):
        for i in range(self._request_num):
            self._future_resp.append(self._executor.submit(self._request))
            # self._executor.submit(self._request)
            self.logger.debug('SUBMIT {0}'.format(i))
        self.logger.debug('SUBMITTED')

    def _request(self):
        param = self._request_queue.popleft()
        conn = self._conns[randrange(len(self._conns))]  # type: HTTP20Connection
        stream_id = conn.request(method=param['method'], url=param['url'], headers=param['headers'])
        self.logger.debug('Send request stream_id: {} index: {} header:  {}'
                          .format(stream_id, param['index'], param['headers']['Range']))
        resp = conn.get_response(stream_id)

        range_header = resp.headers['Content-Range'][0]  # type: bytes
        order = get_order(range_header, self._split_size)
        self.logger.debug(msg='Received response stream_id: {} order: {} header: {}'
                          .format(stream_id, order, range_header))
        # self._result_queue.append({'order': order, 'body': resp.read()})
        return order, resp.read()

    def get_bytes(self):

        for i, future in enumerate(self._future_resp):
            if future.running():
                self.logger.debug('Skipped')
                continue
            else:
                order, body = future.result()
                self.logger.debug(msg='Successfully get result {}'.format(order))
                self._data[order] = body
                self._future_resp.pop(i)

        b = bytearray()
        i = self._received_index
        while i < len(self._data):
            if self._data[i] is None:
                break
            else:
                b += self._data.pop(i)
                i += 1
        self._received_index = i

        return b

    def is_finish(self):
        if self._received_index == self._request_num:
            return False
        else:
            return True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._executor.shutdown()
        return False
