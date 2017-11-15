from concurrent.futures import ThreadPoolExecutor, TimeoutError
from urllib.parse import urlparse, ParseResult
from typing import List
from collections import deque
import random
from logging import getLogger, NullHandler
import gc
import sys
import requests
import time
from requests.exceptions import ConnectionError
from hyper.contrib import HTTP20Adapter
from hyper import HTTPConnection, HTTP20Connection, HTTP11Connection

from .exceptions import PortError, StatusCodeError, NoContentLength, FileSizeError, URIError, NoAcceptRange
from .utils import map_all, get_order, kill_all

local_logger = getLogger(__name__)
local_logger.addHandler(NullHandler())

DEFAULT_SPLIT_SIZE = 1000
DEFAULT_BIAS = 0
DEFAULT_POW = 0
DEFAULT_PARALLEL_NUM = 5


class Downloader(object):
    def __init__(self, urls, split_size=DEFAULT_SPLIT_SIZE, *,
                 parallel_num=DEFAULT_PARALLEL_NUM,
                 logger=local_logger,
                 bias=DEFAULT_BIAS,
                 power=DEFAULT_POW,
                 ):
        """
        :param list urls: URL list
        :param int parallel_num:
        :param int split_size:
        :param logger logger:
        """

        self.logger = logger

        self._bias = bias
        self._power = power
        self._urls = urls.copy()
        default = 1.0 / len(urls)
        self._priority = [default for _ in urls]

        self._length_list = []
        self._conns = [self._check_url(url) for url in urls]
        self._ports = []
        self._index = deque()

        for i in range(len(self._urls)):
            for j in range(parallel_num):
                self._index.append(i)
        random.shuffle(self._index)
        self._url_received_counts = [0 for _ in range(len(self._urls))]

        self._is_started = False

        if map_all(self._length_list) is False:
            raise FileSizeError
        length = int(self._length_list[0])

        if length < split_size:
            self._split_size = length // len(urls)
        else:
            self._split_size = split_size

        begin = 0
        self._request_num = length // split_size
        reminder = length % split_size
        if reminder != 0:
            self._request_num += 1

        self._params = []

        for i in range(self._request_num):

            if reminder != 0 and i == self._request_num - 1:
                end = begin + reminder - 1
            else:
                end = begin + split_size - 1

            param = {'index': i,
                     'method': 'GET',
                     'headers': {'Range': 'bytes={0}-{1}'.format(begin, end)}
                     }
            self._params.append(param)
            begin += split_size

        self._received_index = 0
        self._future_resp = deque()
        self._data = [None for _ in range(self._request_num)]
        self._executor = ThreadPoolExecutor(max_workers=parallel_num * len(self._urls))
        self._return_block_num = []
        self._accumulation = []

        self._plot = []
        self._time = []
        self._exp_data = []
        self._begin_time = time.monotonic()

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

        return self._check_host(url, port)

    def _check_host(self, url, port):
        """
        :param url: str
        :param port: int
        :return: sess
        """

        parsed_url = urlparse(url)  # type: ParseResult

        conn = HTTPConnection(parsed_url.hostname, port=port)
        conn.request('HEAD', url=parsed_url.path)
        resp = conn.get_response()
        status = resp.status

        if 301 <= status <= 303 or 307 <= status <= 308:
            location = resp.headers['Location'][0].decode()
            self._urls.remove(url)
            self._urls.append(location)
            print('Host {} is redirected to {}'.format(url, location), file=sys.stderr)
            conn = self._check_url(url=location)
            conn.request('HEAD', url=location)
            resp = conn.get_response()

        elif status != 200:
            self.logger.debug('Invalid status code: {0}'.format(str(status)))
            raise StatusCodeError

        try:
            length = (resp.headers['Content-Length'][0].decode())
        except KeyError:
            raise NoContentLength

        try:
            resp.headers['Accept-Ranges']
        except KeyError:
            raise NoAcceptRange

        self._length_list.append(length)

        return conn

    def start_download(self):
        for i in range(self._request_num):
            self._future_resp.append(self._executor.submit(self._request))
        self.logger.debug('SUBMITTED')
        self._is_started = True

    def _get_index_rand(self):
        rand = random.random()
        v = 0
        for i, priority in enumerate(self._priority):
            v += priority
            if rand <= v:
                return i

    def _set_priority(self, index, ratio):
        old = self._priority[index]
        new = old * ratio
        if new > 1.0:
            new = 1.0
        diff = old - new
        each = diff / (len(self._priority) - 1)

        c = 0
        for i in range(len(self._priority)):
            if i == index:
                self._priority[i] = new
            else:
                self._priority[i] += each

            if self._priority[i] < 0:
                c += 1
                self._priority[i] = 0

        under = sum(self._priority) - 1.0

        if under != 0:
            u_each = under / (len(self._priority) - c - 1)
            for i in range(len(self._priority)):
                if self._priority[i] != 0 and i != index:
                    self._priority[i] -= u_each

        self.logger.debug('Connection Priority: {}'.format(self._priority))

        if sum(self._priority) > 1.00001:
            self.logger.debug('{}'.format(sum(self._priority)))
            kill_all()

    def _get_param_index(self, index):

        if self._power == 0:
            return 0

        c = self._url_received_counts[index]
        m = max(self._url_received_counts)

        try:
            x = c / m
            # y = int(self._bias * (1.0 - x) ** self._power)
            y = int(self._bias * (1.0 - x ** self._power))
        except ZeroDivisionError:
            y = 0
        return y

    def _request(self):
        index = self._index.pop()

        x = self._get_param_index(index)

        try:
            param = self._params.pop(x)
        except IndexError:
            param = self._params.pop(0)

        conn = self._conns[index]
        url = self._urls[index]
        parsed_url = urlparse(url)
        self.logger.debug('Send request index: {} header:  {}'
                          .format(param['index'], param['headers']['Range']))

        try:
            conn.request(method=param['method'], url=parsed_url.path, headers=param['headers'])
        except ConnectionError as e:
            self.logger.debug('{}'.format(e))

            self._params.insert(0, param)

            self._set_priority(index, 0)
            self._index.append(self._get_index_rand())
            return self._request()

        try:
            resp = conn.get_response()
        except ConnectionResetError:
            self._params.insert(0, param)
            self._set_priority(index, 0)
            self._index.append(self._get_index_rand())
            return self._request()

        status = resp.status
        if status != 206:
            self.logger.debug('Failed {} status {}'.format(self._urls[index], status))

            self._params.insert(0, param)
            self._set_priority(index, 0)
            self._index.append(self._get_index_rand())
            return self._request()

        content = resp.read()
        range_header = resp.headers['Content-Range'][0].decode()
        order = get_order(range_header, self._split_size)
        self.logger.debug(msg='Received response order: {} header: {}'
                          .format(order, range_header))

        self._index.append(index)
        random.shuffle(self._index)
        self._url_received_counts[index] += 1

        self._exp_data.append({'time': time.monotonic() - self._begin_time, 'order': order})

        return order, content

    def get_result(self):
        if self.is_continue() is False:
            return {'exp_data': self._exp_data,
                    'server_result': dict(zip(self._urls, self._url_received_counts)),
                    'return_block_num': self._return_block_num,
                    'accumulation': self._accumulation
                    }

    def get_bytes(self):
        """
        :return: bytes
        """

        if not self._is_started:
            self.start_download()

        i = 0
        while i < len(self._future_resp):
            if self._future_resp[i].running():
                i += 1
            else:
                try:
                    order, content = self._future_resp[i].result(timeout=0)
                    self._data[order] = content
                    del self._future_resp[i]
                    continue
                except TimeoutError:
                    i += 1

        b = bytearray()
        i = self._received_index
        count = 0
        while i < len(self._data):
            if self._data[i] is None:
                break
            else:
                b += self._data[i]
                self._data[i] = None
                i += 1
                count += 1
        self._received_index = i
        if count != 0:
            self._return_block_num.append(count)
            self.logger.debug('Return {} bytes {} blocks'.format(len(b), count))

            accumulation = 0
            for data in self._data:
                if data is not None:
                    accumulation += 1

            self._accumulation.append(accumulation)
        gc.collect()
        return b

    def is_continue(self):
        """
        :return bool: status of downloading
        """
        if self._received_index == self._request_num != 0:
            return False
        else:
            return True

    def close(self):
        self._executor.shutdown()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
